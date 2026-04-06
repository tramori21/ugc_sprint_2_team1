from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_superuser
from db.postgres import get_session
from models.schemas import RoleAssign, RoleCheck, RoleCreate, RoleUpdate
from services.roles_service import RolesService

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    try:
        role = await RolesService.create_role(session, data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e))
    return {"id": str(role.id), "name": role.name}


@router.get("")
async def list_roles(
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    roles = await RolesService.list_roles(session)
    return [{"id": str(r.id), "name": r.name} for r in roles]


@router.patch("/{role_id}")
async def update_role(
    role_id: str,
    data: RoleUpdate,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    try:
        role = await RolesService.update_role(session, role_id, data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    return {"id": str(role.id), "name": role.name}


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    try:
        await RolesService.delete_role(session, role_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    return {"status": "ok"}


@router.post("/assign")
async def assign(
    data: RoleAssign,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    try:
        await RolesService.assign(session, data.user_id, data.role_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    return {"status": "ok"}


@router.post("/revoke")
async def revoke(
    data: RoleAssign,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    try:
        await RolesService.revoke(session, data.user_id, data.role_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
    return {"status": "ok"}


@router.post("/check")
async def check(
    data: RoleCheck,
    _=Depends(require_superuser),
    session: AsyncSession = Depends(get_session),
):
    return {"has_role": await RolesService.check(session, data.user_id, data.role_name)}
