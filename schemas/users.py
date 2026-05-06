from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    balance: Optional[int]
    created_at: datetime
    updated_at: datetime | None
    last_activity_at: datetime | None
    block_status: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None


class SuperUserUpdate(UserUpdate):
    block_status: bool | None = None
