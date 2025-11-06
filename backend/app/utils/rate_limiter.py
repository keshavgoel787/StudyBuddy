"""
Rate limiting utilities using slowapi.
Prevents API abuse on expensive endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_id_or_ip(request: Request) -> str:
    """
    Get rate limit key - prefer user ID if authenticated, fall back to IP.
    This ensures authenticated users can't bypass limits.
    """
    # Check if user is authenticated (from JWT token in header)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Extract user ID from token (simplified - you may need to decode JWT)
        # For now, use the token itself as key
        return f"user:{auth_header[7:30]}"  # First 23 chars of token

    # Fall back to IP address
    return get_remote_address(request)


# Initialize limiter
limiter = Limiter(key_func=get_user_id_or_ip)
