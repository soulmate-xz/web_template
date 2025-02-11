from backend.app.services.user import UserService


async def initialization() -> None:
    """
    项目初始化
    :return:
    """
    await UserService.init_admin()
