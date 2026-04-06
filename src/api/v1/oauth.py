from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.postgres import get_session
from models.schemas import TokenResponse
from models.user import User
from services.oauth_service import OAuthNotConfiguredError, OAuthProviderError, OAuthService

router = APIRouter()

_ALLOWED = {"yandex", "vk", "google"}


@router.get("/{provider}/login")
async def oauth_login(provider: str):
    provider = provider.lower()
    if provider not in _ALLOWED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    try:
        url = OAuthService.build_login_redirect(provider)
    except OAuthNotConfiguredError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except OAuthProviderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    code: str = Query(default=""),
    state: str = Query(default=""),
    session: AsyncSession = Depends(get_session),
):
    provider = provider.lower()
    if provider not in _ALLOWED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    try:
        access, refresh, _ = await OAuthService.finish(provider, code, state, session)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except OAuthNotConfiguredError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except OAuthProviderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{provider}")
async def oauth_unlink(
    provider: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    provider = provider.lower()
    if provider not in _ALLOWED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")
    ok = await OAuthService.unlink(provider, user, session)
    return {"status": "ok", "unlinked": ok}
