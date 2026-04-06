from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.security import hash_password
from db.postgres import get_session
from models.login_history import LoginHistory
from models.schemas import LogoutRequest, ProfileUpdate, RefreshRequest, TokenResponse, UserCreate, UserLogin
from models.user import User
from services.auth_service import AuthService

router = APIRouter()


def _detect_device_type(user_agent: str | None) -> str:
    if not user_agent:
        return "web"
    ua = user_agent.lower()
    if "smart" in ua or "tv" in ua:
        return "smart"
    if "mobile" in ua or "android" in ua or "iphone" in ua or "ipad" in ua:
        return "mobile"
    return "web"


@router.post('/signup', response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
async def signup(
        data: UserCreate,
        session: AsyncSession = Depends(get_session)):
    try:
        access, refresh, _ = await AuthService.register(session, data.login, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post('/login', response_model=TokenResponse)
async def login(
        request: Request,
        data: UserLogin,
        session: AsyncSession = Depends(get_session)):
    try:
        access, refresh, user = await AuthService.login(session, data.login, data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e))

    ip = request.client.host if request.client else None
    ua = request.headers.get('user-agent')
    device_type = _detect_device_type(ua)

    session.add(
        LoginHistory(
            user_id=user.id,
            ip=ip,
            user_agent=ua,
            user_device_type=device_type,
            success=True))
    await session.commit()

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post('/refresh', response_model=TokenResponse)
async def refresh(
        data: RefreshRequest,
        session: AsyncSession = Depends(get_session)):
    try:
        access, refresh, _ = await AuthService.refresh(session, data.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post('/logout')
async def logout(
        data: LogoutRequest,
        session: AsyncSession = Depends(get_session)):
    await AuthService.logout(session, data.refresh_token)
    return {'status': 'ok'}


@router.get("/profile")
async def get_profile(current_user=Depends(get_current_user)):
    return current_user


@router.patch('/profile')
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if data.login and data.login != user.login:
        exists = (await session.execute(select(User).where(User.login == data.login))).scalar_one_or_none()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Login already exists')
        user.login = data.login

    if data.password:
        user.password = hash_password(data.password)

    session.add(user)
    await session.commit()
    return {'status': 'ok'}


@router.get('/login-history')
async def login_history(
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == user.id)
        .order_by(LoginHistory.created_at.desc())
        .limit(20)
    )
    items = res.scalars().all()
    return [{'ip': i.ip,
             'user_agent': i.user_agent,
             'success': i.success,
             'created_at': i.created_at.isoformat()} for i in items]
