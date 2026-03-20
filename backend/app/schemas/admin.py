from pydantic import BaseModel, EmailStr
from typing import Literal


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "user", "viewer"]


class InviteAcceptRequest(BaseModel):
    token: str
    email: EmailStr
    password: str
    display_name: str