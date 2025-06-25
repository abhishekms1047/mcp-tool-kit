import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class AuthService:
    """Basic OAuth2 authentication service."""

    def __init__(self):
        self.users: Dict[str, str] = {"admin": "admin"}
        self.tokens: Dict[str, Dict[str, datetime]] = {}
        self.expiry_minutes = 60

    def authenticate_user(self, username: str, password: str) -> bool:
        return self.users.get(username) == password

    def create_token(self, username: str) -> str:
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "username": username,
            "expires": datetime.utcnow() + timedelta(minutes=self.expiry_minutes),
        }
        logging.debug(f"Token created for {username}")
        return token

    def verify_token(self, token: str) -> str:
        info = self.tokens.get(token)
        if not info:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        if info["expires"] < datetime.utcnow():
            del self.tokens[token]
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Token expired")
        return info["username"]


auth_service = AuthService()


async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password flow endpoint."""
    if not auth_service.authenticate_user(form_data.username, form_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    token = auth_service.create_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}


def verify_token(token: str) -> str:
    """Verify an OAuth2 token and return username."""
    return auth_service.verify_token(token)
