from DRcode.app.libs.error_code import Success, DeleteSuccess, NotFound, InstructBusy, ServerError
from DRcode.app.libs.redprint import Redprint
from DRcode.app.validators.forms import CodeForm
from flask import jsonify
import os
from DRcode.app.config.setting import CODE_PATH_USER
import DRcode.app.libs.global_var as gl
from DRcode.app.libs.token_auth import auth

api = Redprint('codes')


@api.route('')
def get_code_list():
    try:
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        return jsonify(robot.code_user_list), 200
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))


@api.route('', methods=['POST'])
# @auth.login_required
def create_code():
    if gl.get_value('state') == 'WAITING':
        gl.set_value('state', 'BUSY')
        form = CodeForm().validate_for_api()
        try:
            from DRcode.app.libs.robot import Robot
            Robot.robot_add_code(form.name.data, form.body.data)
            gl.set_value('state', 'WAITING')
            return Success()
        except Exception as result:
            print('检测出异常{}'.format(result))
            return ServerError(msg='Error{}'.format(result))
    else:
        return InstructBusy()


@api.route('/<code_name>')
# @auth.login_required
def get_code(code_name):
    code = {'name': code_name, 'body': ''}
    path = CODE_PATH_USER + code_name + '.py'
    if os.path.isfile(path):
        instruct = 'cat ' + path
        try:
            code['body'] = os.popen(instruct).read()
            return jsonify(code), 200
        except Exception as result:
            print('检测出异常{}'.format(result))
            return ServerError()
    else:
        raise NotFound()


@api.route('/<code_name>', methods=['PUT'])
# @auth.login_required
def edit_code(code_name):
    if gl.get_value('state') == 'WAITING':
        gl.set_value('state', 'BUSY')
        form = CodeForm().validate_for_api()
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        # 动作不存在
        if code_name not in robot.code_user_list:
            gl.set_value('state', 'WAITING')
            return NotFound()
        # 重命名并修改动作
        else:
            try:
                # 仅修改名称
                if form.body.data == '':
                    new_name = form.name.data
                    Robot.robot_rename_code(code_name, new_name)
                # 仅修改内容
                elif form.name.data == '':
                    Robot.robot_delete_code(code_name)
                    Robot.robot_add_code(code_name, form.body.data)
                # 都修改
                else:
                    Robot.robot_delete_code(code_name)
                    Robot.robot_add_code(form.name.data, form.body.data)
                gl.set_value('state', 'WAITING')
                return Success(msg='rename and edit successfully')
            except Exception as result:
                print('检测出异常{}'.format(result))
                gl.set_value('state', 'WAITING')
                return ServerError(msg='Error{}'.format(result))
    else:
        return InstructBusy()


@api.route('/<code_name>', methods=['DELETE'])
# @auth.login_required
def delete_code(code_name):
    if gl.get_value('state') == 'WAITING':
        gl.set_value('state', 'BUSY')
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        if code_name not in robot.code_user_list:
            gl.set_value('state', 'WAITING')
            return NotFound()
        else:
            try:
                Robot.robot_delete_code(code_name)
                gl.set_value('state', 'WAITING')
                return DeleteSuccess()
            except Exception as result:
                print('检测出异常{}'.format(result))
                gl.set_value('state', 'WAITING')
                return ServerError(msg='Error{}'.format(result))
    else:
        return InstructBusy()
