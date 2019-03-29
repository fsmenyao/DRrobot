from werkzeug.security import generate_password_hash, check_password_hash
from DRcode.app.libs.error_code import AuthFailed
from DRcode.app.config.secure import ROBOT_ID, SYS_PASSWORD, PASSWORD_PATH
import os


class Password:

    def __init__(self):
        self.sys_nickname = ROBOT_ID
        self.sys_password = SYS_PASSWORD
        f = os.open(PASSWORD_PATH, os.O_RDWR)
        user = str(os.read(f, 500), encoding="utf-8").split('\r\n')
        user_nickname = user[0]
        user_password = user[1]
        os.close(f)
        self.fields = ['user_nickname', 'user_password']
        self.user_nickname = user_nickname
        self.user_password = user_password

    @staticmethod
    def write_password(nickname, password):
        try:
            f = os.open(PASSWORD_PATH, os.O_RDWR | os.O_TRUNC)
            user = nickname + '\r\n' + password
            os.write(f, bytes(user, 'utf-8'))
            os.close(f)
            return True
        except:
            return False

    def verify(self, nickname, secret):
        if nickname == self.sys_nickname and secret == self.sys_password:
            password = self.sys_password
        elif nickname == self.user_nickname and secret == self.user_password:
            password = self.user_password
        else:
            raise AuthFailed()
        return {'key': password}

