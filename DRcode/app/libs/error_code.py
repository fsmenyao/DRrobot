from DRcode.app.libs.error import APIException


class Success(APIException):
    code = 201
    msg = 'create successfully'


class DeleteSuccess(Success):
    code = 204
    msg = 'delete successfully'


class InstructSuccess(Success):
    code = 204
    msg = 'execute instruction successfully'


class InstructBusy(APIException):
    code = 503
    msg = 'sorry, another program is running.'


class InstructFailed(APIException):
    code = 500
    msg = 'execute instruction failed'


class ServerError(APIException):
    code = 500
    msg = 'sorry, we made a mistake (*￣︶￣)!'


class ClientTypeError(APIException):
    code = 400
    msg = 'client is invalid'


class ParameterException(APIException):
    code = 400
    msg = 'invalid parameter'


class NotFound(APIException):
    code = 404
    msg = 'the resource are not found O__O...'


class AuthFailed(APIException):
    code = 401
    msg = 'authorization failed'


class Forbidden(APIException):
    code = 403
    msg = 'forbidden, not in scope'

