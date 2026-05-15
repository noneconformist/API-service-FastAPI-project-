import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

import redis.asyncio as redis
import uvloop
from authx import AuthX, AuthXConfig, RequestToken
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from change_password import router as change_password_router
from core import pwd_context
from database import get_db
from exceptions import register_exception_handlers
from log_config import ENV, setup_logging
from models import Role, User
from schemas.password_str import PasswordStr
from schemas.users import SuperUserUpdate, UserOut, UserUpdate
from support import format_balance

try:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:
    print('Warning: uvloop failed to set as main event loop')


app = FastAPI()

# Logging
setup_logging(ENV)

# REDIS
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
# redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=5)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_client = redis.from_url(
    f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
    retry_on_timeout=True,
    max_connections=20,
)

register_exception_handlers(app)
app.include_router(change_password_router, tags=['password'])

config = AuthXConfig()
config.JWT_SECRET_KEY = 'FASTAPI_SECRET_KEY'
config.JWT_ACCESS_COOKIE_NAME = 'access_token'
config.JWT_TOKEN_LOCATION = ['headers']
config.JWT_COOKIE_CSRF_PROTECT = os.getenv('JWT_COOKIE_CSRF_PROTECT', 'True') == 'True'

security = AuthX(config=config)

# token's lifetime
ACCESS_TOKEN_EXPIRE = timedelta(minutes=1)
REFRESH_TOKEN_EXPIRE = timedelta(minutes=2)

config.JWT_ACCESS_TOKEN_EXPIRES = ACCESS_TOKEN_EXPIRE
config.JWT_REFRESH_TOKEN_EXPIRES = REFRESH_TOKEN_EXPIRE


class UserSchema(BaseModel):
    email: EmailStr
    password: PasswordStr
    is_superuser: bool | None = None


@app.post('/register')
async def register(credentials: UserSchema, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    existing_user = result.scalars().first()

    # If the email already exists and the account has not been deleted → error
    if existing_user and existing_user.is_active:
        raise HTTPException(status_code=400, detail='Email already registered')

    # Hashing the password
    hashed_password = pwd_context.hash(credentials.password)

    new_user = User(
        email=str(credentials.email),
        password=hashed_password,
        is_superuser=credentials.is_superuser,
        created_at=datetime.now(timezone.utc),
        is_active=True,
    )

    # Admin's balance = 0
    format_balance(new_user)

    role_result = await db.execute(select(Role).where(Role.name == 'user'))
    default_role = role_result.scalars().first()
    if not default_role:
        default_role = Role(name='user')
        db.add(default_role)
        await db.commit()
        await db.refresh(default_role)

    new_user.roles.append(default_role)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {'msg': 'User registered successfully'}


@app.post('/login')
async def login(credentials: UserSchema, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == credentials.email, User.is_active.is_(True))
    )
    user = result.scalars().first()

    # soft delete check
    if not user:
        raise HTTPException(status_code=404, detail='This account does not exist')

    if not user.is_active:
        raise HTTPException(status_code=404, detail='This account has been deleted')

    # Block check
    if user.block_status:
        raise HTTPException(status_code=403, detail='This account has been blocked')

    if user and pwd_context.verify(credentials.password, user.password):
        # Update last_activity_at
        user.last_activity_at = datetime.now(timezone.utc)
        user.balance += 15
        await db.commit()
        await db.refresh(user)

        access_token = security.create_access_token(
            subject=credentials.email,
            uid=str(credentials.email),
            expires_delta=ACCESS_TOKEN_EXPIRE,
            additional_claims={'jti': str(uuid4())},
        )

        # Get jti from access token
        access_token_obj = RequestToken(token=access_token, type='access', location='headers')
        payload = security.verify_token(access_token_obj, verify_csrf=False)
        jti = getattr(payload, 'jti', None) or (
            payload.get('jti') if isinstance(payload, dict) else None
        )

        if jti:
            await redis_client.setex(
                f'access_token:{jti}', int(ACCESS_TOKEN_EXPIRE.total_seconds()), access_token
            )

        refresh_token = security.create_refresh_token(
            subject=credentials.email,
            uid=str(credentials.email),
            expires_delta=REFRESH_TOKEN_EXPIRE,
            additional_claims={'jti': str(uuid4())},
        )

        # Get jti from refresh token
        refresh_token_obj = RequestToken(token=refresh_token, type='refresh', location='headers')
        payload = security.verify_token(refresh_token_obj, verify_csrf=False)
        jti = getattr(payload, 'jti', None) or (
            payload.get('jti') if isinstance(payload, dict) else None
        )

        if jti:
            await redis_client.setex(
                f'refresh_token:{jti}', int(REFRESH_TOKEN_EXPIRE.total_seconds()), refresh_token
            )

        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=int(ACCESS_TOKEN_EXPIRE.total_seconds()),
        )

        return {'access_token': access_token, 'refresh_token': refresh_token}

    raise HTTPException(status_code=401, detail='Incorrect email or password')


@app.post('/logout')
async def logout(response: Response, request: Request):
    # Adding a token to a blacklist with automatic TTL
    token: RequestToken | None = await security.get_access_token_from_request(request)

    # Add token into blacklist
    if token and token.token:
        payload = security.verify_token(token, verify_csrf=False)

        jti = getattr(payload, 'jti', None)
        if not jti and isinstance(payload, dict):
            jti = payload.get('jti')

        if jti:
            ttl = int(ACCESS_TOKEN_EXPIRE.total_seconds()) + 60  # reserve 60 sec
            await redis_client.setex(f'blacklist:{jti}', ttl, 'revoked')

    # Deleting cookies from the client
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    return {'msg': 'Logged out successfully'}


@app.post('/refresh')
async def refresh_tokens(user=Depends(security.refresh_token_required), response: Response = None):
    subject = user.sub
    uid = subject

    # Generation new token pairs
    new_access_token = security.create_access_token(
        subject=subject,
        uid=uid,
        expires_delta=ACCESS_TOKEN_EXPIRE,
    )
    new_refresh_token = security.create_refresh_token(
        subject=subject,
        uid=uid,
        expires_delta=REFRESH_TOKEN_EXPIRE,
    )

    # Set new access_token into the cookie
    if response:
        response.set_cookie(
            config.JWT_ACCESS_COOKIE_NAME,
            new_access_token,
        )

    return {
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
    }


# The depends on instead security.access_token_required
async def current_user_with_blacklist(
    user=Depends(security.access_token_required),
):
    jti = getattr(user, 'jti', None) or (user.get('jti') if isinstance(user, dict) else None)
    if jti:
        if await redis_client.exists(f'blacklist:{jti}'):
            raise HTTPException(
                status_code=401, detail='Token has been revoked. Please login again.'
            )

    return user


@app.get('/protected')
async def protected(user=Depends(current_user_with_blacklist)):
    return {'data': 'A secret for logged in users', 'user': user}


async def get_current_superuser(
    user=Depends(current_user_with_blacklist), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()
    if not db_user or not db_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Superuser privileges required'
        )
    return db_user


async def get_current_admin_or_superuser(
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    if db_user.is_superuser or any(role.name == 'admin' for role in db_user.roles):
        return db_user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')


@app.get('/users', response_model=List[UserOut])
async def list_users(
    id: Optional[int] = Query(None),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    block_status: Optional[bool] = Query(None),
    deleted_only: bool = Query(False, description='Return only soft-deleted users'),
    sort_by: str = Query('id', pattern='^(id|balance|last_activity_at)$'),
    direction: Optional[str] = Query('asc', pattern='^(asc|desc)$'),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin_or_superuser),  # checking access rights
) -> List[User]:
    # Basic query
    stmt = select(User)

    # Filtering deleted users
    if deleted_only:
        stmt = stmt.where(User.is_active.is_(False))
    else:
        stmt = stmt.where(User.is_active.is_(True))

    # Filtering
    if id is not None:
        stmt = stmt.where(User.id == id)
    if first_name is not None:
        stmt = stmt.where(User.first_name.ilike(f'%{first_name}%'))
    if last_name is not None:
        stmt = stmt.where(User.last_name.ilike(f'%{last_name}%'))
    if block_status is not None:
        stmt = stmt.where(User.block_status == block_status)

    # Sorting
    sort_column = getattr(User, sort_by)
    if direction == 'asc':
        stmt = stmt.order_by(asc(sort_column))
    else:
        stmt = stmt.order_by(desc(sort_column))

    result = await db.execute(stmt)
    users = list(result.scalars().all())
    return users


@app.get('/', include_in_schema=False)
async def root():
    return {
        'message': 'API is running',
        'docs': '/docs',
        'register': '/register (POST)',
        'login': '/login (POST)',
    }


@app.get('/me', response_model=UserOut)
async def get_me(
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()

    # Update last_activity_at
    db_user.last_activity_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_user)

    if not db_user.first_name or not db_user.last_name:
        raise HTTPException(
            status_code=400, detail='Profile data incomplete: first_name and last_name required'
        )

    db_user.balance = format_balance(db_user)

    return db_user


@app.patch('/me', response_model=UserOut)
async def update_me(
    update_data: UserUpdate,
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)

    # Admin's balance = 0
    format_balance(db_user)

    # renew updated_at
    db_user.updated_at = datetime.now(timezone.utc)
    db_user.last_activity_at = datetime.now(timezone.utc)

    # Admin's balance = 0
    if any(role.name == 'admin' for role in db_user.roles):
        db_user.balance = 0

    await db.commit()
    await db.refresh(db_user)
    return {**db_user.__dict__, 'balance': format_balance(db_user)}


# superuser can patch profiles
@app.patch('/users/{id}/profile', response_model=UserOut)
async def update_user_profile(
    update_data: SuperUserUpdate,
    id: int = Path(..., description='ID user'),
    _: User = Depends(get_current_superuser),  # Check access superuser
    db: AsyncSession = Depends(get_db),
):
    # Find user by id
    result = await db.execute(select(User).where(User.id == id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail=f'User with id={id} not found')

    # Update fields (included block_status)
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_user, field, value)

    # Admin's balance = 0
    format_balance(db_user)

    # renew updated_at
    db_user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_user)
    return db_user


# user can delete own profile
@app.delete('/me')
async def delete_me(
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()

    # The admin cannot delete the own profile
    if any(role.name == 'admin' for role in db_user.roles):
        raise HTTPException(status_code=403, detail='Admin cannot delete own profile')

    db_user.is_active = False
    await db.commit()
    return {'detail': 'Your profile deleted successfully'}


# superuser can delete profiles
@app.delete('/users/{id}/profile')
async def delete_user_profile(
    id: int = Path(..., description='ID user'),
    _: User = Depends(get_current_superuser),  # Check access superuser
    db: AsyncSession = Depends(get_db),
):
    # Find user by id
    result = await db.execute(select(User).where(User.id == id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail=f'User with id={id} not found')

    db_user.is_active = False
    await db.commit()
    return {'detail': f'User with id={id} deleted successfully'}


# Get balance
@app.get('/me/balance')
async def get_balance(
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()

    # Update last_activity_at
    db_user.last_activity_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_user)

    if not db_user.first_name or not db_user.last_name:
        raise HTTPException(
            status_code=400, detail='Profile data incomplete: first_name and last_name required'
        )

    return {'balance': format_balance(db_user)}


# Charge balance
@app.put('/me/balance')
async def put_balance(
    user=Depends(current_user_with_blacklist),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user.sub))
    db_user = result.scalars().first()

    if not db_user.first_name or not db_user.last_name:
        raise HTTPException(
            status_code=400, detail='Profile data incomplete: first_name and last_name required'
        )

    # Update last_activity_at
    db_user.last_activity_at = datetime.now(timezone.utc)

    # Attempt to charge funds
    if any(role.name == 'admin' for role in db_user.roles):
        return {
            'message': 'Admins cannot have an active balance',
            'balance': format_balance(db_user),
        }

    if db_user.balance >= 10:
        db_user.balance -= 10
        await db.commit()
        await db.refresh(db_user)
        return {
            'message': '10 has been charged from your balance',
            'balance': format_balance(db_user),
        }
    else:
        await db.commit()  # for last_activity_at only
        raise HTTPException(
            status_code=400, detail=f'Insufficient funds. Balance: {db_user.balance}'
        )


# block users
@app.patch('/users/{id}/block')
async def block_unblock_user(
    id: int = Path(..., description="User's ID"),
    block: bool = Query(..., description='True = block, False = unblock'),
    _: User = Depends(get_current_admin_or_superuser),  # проверка прав
    db: AsyncSession = Depends(get_db),
):
    # Find user
    result = await db.execute(select(User).where(User.id == id))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail=f'User with id={id} not found')

    # Update block status
    db_user.block_status = block
    db_user.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_user)

    action = 'blocked' if block else 'unblocked'
    return {'detail': f'User with id={id} has been {action} successfully'}
