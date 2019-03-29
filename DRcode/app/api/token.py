from flask import current_app, jsonify
from DRcode.app.libs.error_code import AuthFailed
from DRcode.app.libs.redprint import Redprint
from DRcode.app.validators.forms import TokenForm, TokenInfoForm
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, \
    BadSignature

api = Redprint('token')


@api.route('', methods=['POST'])
def get_token():
    from DRcode.app.libs.password import Password
    form = TokenForm().validate_for_api()
    identity = Password().verify(form.nickname.data, form.secret.data)
    expiration = current_app.config['TOKEN_EXPIRATION']
    token = generate_auth_token(identity['key'], expiration)
    t = {
        'token': token.decode('ascii')
    }
    return jsonify(t), 201


@api.route('/content', methods=['POST'])
def get_token_info():
    form = TokenInfoForm().validate_for_api()
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(form.token.data, return_header=True)
        print(data[1])
    except SignatureExpired:
        raise AuthFailed(msg='token is expired')
    except BadSignature:
        raise AuthFailed(msg='token is invalid')
    r = {
        'create_at': data[1]['iat'],
        'expire_in': data[1]['exp'],
    }
    return jsonify(r), 200


def generate_auth_token(key, expiration=7200):
    s = Serializer(current_app.config['SECRET_KEY'],
                   expires_in=expiration)
    return s.dumps({
        'key': key
    })
