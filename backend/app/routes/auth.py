from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.user_token import UserToken
from app.schemas.auth import TokenResponse, UserResponse
from app.utils.auth_middleware import create_access_token
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Google OAuth configuration
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.readonly'
]


@router.get("/google")
async def google_auth():
    """
    Initiate Google OAuth flow.
    Redirects user to Google's consent screen.
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri]
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )

    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    Exchanges code for tokens, creates/updates user, returns JWT.
    """
    try:
        # Exchange authorization code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.google_redirect_uri
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Verify and decode ID token to get user info
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            settings.google_client_id
        )

        google_id = id_info['sub']
        email = id_info['email']
        name = id_info.get('name', email.split('@')[0])

        # Check if user exists
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Store/update tokens
        user_token = db.query(UserToken).filter(UserToken.user_id == user.id).first()

        if user_token:
            # Update existing tokens
            user_token.access_token = credentials.token
            user_token.refresh_token = credentials.refresh_token or user_token.refresh_token
            user_token.token_expiry = credentials.expiry
        else:
            # Create new token record
            user_token = UserToken(
                user_id=user.id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=credentials.expiry
            )
            db.add(user_token)

        db.commit()

        # Create JWT for our app
        jwt_token = create_access_token(str(user.id))

        # Redirect to frontend with token
        redirect_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
