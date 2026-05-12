import secrets
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import pwd_context
from database import get_db
from models import User
from schemas.password_str import PasswordStr

router = APIRouter()

# Temporary storage of reset tokens
reset_tokens: dict[str, tuple[str, float]] = {}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: PasswordStr


@router.post('/forgot-password')
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == str(request.email)))
    existing_user = result.scalars().first()
    if existing_user:
        token = secrets.token_urlsafe(32)
        reset_tokens[token] = (request.email, time.time())
        return {'detail': 'Reset token generated', 'token': token}
    return {'detail': 'If the user exists, a reset token is sent.'}


@router.post('/reset-password')
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_data = reset_tokens.get(request.token)
    if not token_data:
        raise HTTPException(status_code=400, detail='RESET_PASSWORD_BAD_TOKEN')

    email, ts = token_data
    if time.time() - ts > 900:
        del reset_tokens[request.token]
        raise HTTPException(status_code=400, detail='RESET_PASSWORD_BAD_TOKEN')

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    user.password = pwd_context.hash(request.password)
    await db.commit()
    del reset_tokens[request.token]
    return {'detail': 'Password successfully changed'}
