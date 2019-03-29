from DRcode.app.libs.error_code import NotFound, ServerError
from DRcode.app.libs.redprint import Redprint
from DRcode.app.validators.forms import CodeForm
from flask import jsonify

import os

from DRcode.app.config.setting import CODE_PATH_USER
import DRcode.app.libs.global_var as gl
from DRcode.app.libs.token_auth import auth

api = Redprint('output')

@api.route('')
# @auth.login_required
def get_output():
    code = {'output': ''}
    path = '/home/pi/DRrobot/output.py'
    if os.path.isfile(path):
        instruct = 'sed \'s/\\x0//g\' ' + path
        #instruct = 'cat -A ' + path + ' |sed \'s/[\^@]//g\''
        try:
            code['output'] = os.popen(instruct).read()
            cmd_ = 'cat /dev/null > ' + path
            os.popen(cmd_)
            return jsonify(code), 200
        except Exception as result:
            print('检测出异常{}'.format(result))
            return ServerError()
    else:
        raise NotFound()

