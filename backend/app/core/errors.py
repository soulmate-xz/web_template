class ApplicationError(Exception):
    code = 200
    message = "你的请求发生了错误，请稍后再试。"


class NotFilterApi(ApplicationError):
    code = 404
    message = "目标路由不存在或暂不支持条件筛选器，请检查后重试。"


class UserAuthFailed(ApplicationError):
    code = 403
    message = "用户名或密码错误"


class UserLoginFailed(ApplicationError):
    headers = {"WWW-Authenticate": "Bearer"}
    code = 401
    message = "用户未登录"


class UserTokenWasExpired(ApplicationError):
    headers = {"WWW-Authenticate": "Bearer"}
    code = 401
    message = "用户验证信息有误或已过期，请重新登录"


class UserTokenWasUpdated(ApplicationError):
    headers = {"WWW-Authenticate": "Bearer"}
    code = 401
    message = "检测到账号已在其他地方登录，请重新登录"


class UserWasAlreadyDisabled(ApplicationError):
    code = 401
    message = "该账户已禁用，请联系管理员"


class UserVerifyFailed(ApplicationError):
    code = 403
    message = "当前账号密码验证失败"


class UserNameNotFound(ApplicationError):
    code = 403
    message = "未找到指定用户"
