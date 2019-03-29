from DRcode.app.libs.error_code import Success, ServerError
from DRcode.app.libs.redprint import Redprint
from DRcode.app.validators.forms import PasswordForm

api = Redprint('password')


@api.route('', methods=['POST'])
# @auth.login_required
def create_password():
    from DRcode.app.libs.password import Password
    password = Password()
    form = PasswordForm().validate_for_api()
    try:
        password.write_password(form.nickname.data, form.secret.data)
        return Success()
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))


