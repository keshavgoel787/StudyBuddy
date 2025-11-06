"""
Utility functions for managing and refreshing Google OAuth tokens.
"""
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session

from app.models.user_token import UserToken
from app.config import get_settings

settings = get_settings()


def is_token_expired(user_token: UserToken) -> bool:
    """
    Check if the access token is expired or about to expire.

    Args:
        user_token: UserToken object

    Returns:
        True if token is expired or expiring within 5 minutes
    """
    if not user_token.token_expiry:
        # No expiry info - assume expired to be safe
        return True

    # Add 5 minute buffer before actual expiry
    buffer = timedelta(minutes=5)
    now = datetime.utcnow()

    # Make token_expiry timezone-naive if it's timezone-aware
    expiry = user_token.token_expiry
    if expiry.tzinfo is not None:
        expiry = expiry.replace(tzinfo=None)

    return now + buffer >= expiry


def refresh_access_token(user_token: UserToken, db: Session) -> UserToken:
    """
    Refresh the Google OAuth access token using the refresh token.

    Args:
        user_token: UserToken object with refresh_token
        db: Database session

    Returns:
        Updated UserToken object

    Raises:
        Exception if refresh fails
    """
    if not user_token.refresh_token:
        raise Exception("No refresh token available")

    try:
        # Create credentials object
        creds = Credentials(
            token=user_token.access_token,
            refresh_token=user_token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret
        )

        # Refresh the token
        creds.refresh(Request())

        # Update database
        user_token.access_token = creds.token
        if creds.expiry:
            user_token.token_expiry = creds.expiry

        db.commit()
        db.refresh(user_token)

        return user_token

    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to refresh token: {str(e)}")


def get_valid_user_token(user_token: UserToken, db: Session) -> UserToken:
    """
    Get a valid (non-expired) user token, refreshing if necessary.

    Args:
        user_token: UserToken object
        db: Database session

    Returns:
        UserToken object with valid access_token

    Raises:
        Exception if token cannot be refreshed
    """
    if is_token_expired(user_token):
        user_token = refresh_access_token(user_token, db)

    return user_token
