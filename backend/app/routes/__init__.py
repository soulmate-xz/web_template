from fastapi import APIRouter

from backend.app.routes.user import router as user_router

router = APIRouter()
router.include_router(user_router, tags=["用户管理"], prefix="/user")
