from fastapi import APIRouter

from backend.app.core.schemas.user import UserPageListRequest, UserPageListResponse
from backend.app.services.user import UserService

router = APIRouter()


@router.post(
    "/list",
    name="用户列表",
    response_model=UserPageListResponse,
)
async def list_user(page_request: UserPageListRequest):
    return await UserService.list_user(page_request)
