from collections import namedtuple
from flask import current_app, g
from flask_httpauth import HTTPBasicAuth
from itsdangerous import TimedJSONWebSignatureSerializer \
    as Serializer, BadSignature, SignatureExpired
from DRcode.app.libs.error_code import AuthFailed

auth = HTTPBasicAuth()
Password = namedtuple('Password', ['key'])


@auth.verify_password
def verify_password(token, secret):
    password_info = verify_auth_token(token)
    if not password_info:
        return False
    else:
        # request
        g.user = password_info
        return True


def verify_auth_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except BadSignature:
        raise AuthFailed(msg='token is invalid')
    except SignatureExpired:
        raise AuthFailed(msg='token is expired')
    key = data['key']
    return Password(key)
