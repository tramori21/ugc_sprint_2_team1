from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from core.security import hash_password, verify_password
from db.postgres import get_session
from models.schemas import ChangeLoginRequest, ChangePasswordRequest
from models.user import User

router = APIRouter()


@router.put('/me/password', status_code=HTTPStatus.NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not verify_password(payload.old_password, user.password):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='invalid credentials',
        )

    user.password = hash_password(payload.new_password)
    session.add(user)
    await session.commit()
    return


@router.put('/me/login', status_code=HTTPStatus.NO_CONTENT)
async def change_login(
    payload: ChangeLoginRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    new_login = payload.new_login.strip()
    if not new_login:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail='login is empty',
        )

    res = await session.execute(select(User).where(User.login == new_login))
    exists = res.scalar_one_or_none()
    if exists and exists.id != user.id:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='login already exists',
        )

    user.login = new_login
    session.add(user)
    await session.commit()
    return
