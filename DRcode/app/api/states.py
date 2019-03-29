from flask import jsonify
from DRcode.app.libs.error_code import ServerError
from DRcode.app.libs.redprint import Redprint
import DRcode.app.libs.global_var as gl
import os

api = Redprint('states')


@api.route('')
def get_states():
    from DRcode.app.libs.robot import Robot
    try:
        states = Robot().robot_get_states()
        return jsonify(states), 200
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))


@api.route('/close')
def close_robot():
    os.system("sudo shutdown -h now")
