"""User request/response models."""

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Fields required to register a new user."""

    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    """Fields required to login a user."""

    email: str
    password: str