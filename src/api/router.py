from fastapi import APIRouter

from api.v1 import auth, oauth, roles, ugc, users

router = APIRouter()
router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
router.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
router.include_router(users.router, prefix="/api/v1/users", tags=["users"])
router.include_router(oauth.router, prefix="/api/v1/oauth", tags=["oauth"])
router.include_router(ugc.router, prefix="/api/v1/ugc", tags=["ugc"])
