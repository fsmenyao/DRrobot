from flask import jsonify
from DRcode.app.libs.error_code import InstructSuccess, InstructFailed, InstructBusy, ParameterException, ServerError
from DRcode.app.libs.redprint import Redprint
from DRcode.app.libs.instructs import Instruct
from DRcode.app.validators.forms import InstructForm, FrameForm
from DRcode.app.libs.enums import InstructTypeEnum
import DRcode.app.libs.global_var as gl

api = Redprint('instructs')


@api.route('', methods=['POST'])
def execute():
    if gl.get_value('state') == 'PAUSE':
        form = InstructForm().validate_for_api()
        promise = {
            InstructTypeEnum.STOP: __execute_stop,
            InstructTypeEnum.CONTINUE: __execute_continue
        }
        if form.instruct_type.data in promise:
            # print('instrcut in-----------')
            try:
                if promise[form.instruct_type.data]():
                    return InstructSuccess()
                else:
                    return InstructFailed()
            except Exception as result:
                print('检测出异常{}'.format(result))
                gl.set_value('state', 'WAITING')
                return ServerError(msg='Error{}'.format(result))
        else:
            print('server in PAUSE------------------')
            return InstructBusy(msg='the robot is in PUASE state')
    elif gl.get_value('state') == 'WAITING':
        # print('WAITING------------------')
        form = InstructForm().validate_for_api()
        promise = {
            InstructTypeEnum.STOP: __execute_stop,
            InstructTypeEnum.ACTION_FRAME: __execute_read_action_frame,
            InstructTypeEnum.ACTION_FRAME_SHOW: __execute_show_action_frame,
            InstructTypeEnum.ACTION_SHOW_SYS: __execute_action_show_sys,
            InstructTypeEnum.ACTION_SHOW_USER: __execute_action_show_user,
            InstructTypeEnum.CODE_SHOW_SYS: __execute_code_show_sys,
            InstructTypeEnum.CODE_SHOW_USER: __execute_code_show_user,
            InstructTypeEnum.VOICE: __execute_voice,
            # By YJY
            InstructTypeEnum.SHOW_CODE_FRAME: __execute_show_code_frame,
            InstructTypeEnum.MODE: __execute_mode,
            InstructTypeEnum.ANGLE: __execute_angle,
            InstructTypeEnum.DEMARCATE: __execute_demarcate
        }
        if form.instruct_type.data in promise:
            # print('instrcut in-----------')
            try:
                done = promise[form.instruct_type.data]()
                if form.instruct_type.data == InstructTypeEnum.ACTION_FRAME:
                    if done:
                        return jsonify(done)
                    else:
                        return InstructFailed()
                else:
                    if done:
                        return InstructSuccess()
                    else:
                        return InstructFailed()
            except KeyboardInterrupt:
                print("动作急停!!!")
                gl.set_value('state', 'WAITING')
                return InstructBusy(msg='instruction has been stopped!')
            except Exception as result:
                print('检测出异常{}'.format(result))
                gl.set_value('state', 'WAITING')
                return ServerError(msg='Error{}'.format(result))
        else:
            print('server in WAITING------------------')
            return InstructBusy(msg='the robot is in WAITING state')
    elif gl.get_value('state') == 'BUSY':
        # print('BUSY------------------')
        form = InstructForm().validate_for_api()
        promise = {
            InstructTypeEnum.STOP: __execute_stop,
            InstructTypeEnum.PAUSE: __execute_pause
        }
        if form.instruct_type.data in promise:
            # print('instrcut in-----------')
            try:
                done = promise[form.instruct_type.data]()
                if done:
                    return InstructSuccess()
                else:
                    return InstructFailed()
            except Exception as result:
                print('检测出异常{}'.format(result))
                gl.set_value('state', 'WAITING')
                return ServerError(msg='Error{}'.format(result))
        else:
            print('server in BUSY------------------')
            # print('instrcut out-----------')
            return InstructBusy(msg='the robot is in BUSY state')
    else:
        print(gl.get_value('state'))
        return ParameterException()


def __execute_stop():
    if gl.get_value('state') == 'WAITING':
        Instruct().execute_stop()
    else:
        gl.set_value('state', 'STOP')
        Instruct.execute_stop_music()
    return True


def __execute_reset():
    gl.set_value('state', 'WAITING')
    return True


def __execute_pause():
    gl.set_value('state', 'PAUSE')
    return True


def __execute_continue():
    gl.set_value('state', 'BUSY')
    return True


def __execute_read_action_frame():
    gl.set_value('state', 'BUSY')
    frames = Instruct().execute_read_action_frame()
    gl.set_value('state', 'WAITING')
    if frames:
        return frames
    else:
        return False


def __execute_show_action_frame():
    # 执行动作帧的临时文件保存到系统action路径下
    from DRcode.app.libs.robot import Robot
    if gl.get_value('state') == 'WAITING':
        gl.set_value('state', 'BUSY')
        form = FrameForm().validate_for_api()
        action_temp_name = 'action_frame_temp'
        Robot.robot_add_action(action_temp_name, form.para1.data, path='sys')
        done = Instruct.execute_action_show(action_temp_name, num=0, speed=form.para2.data)
        gl.set_value('state', 'WAITING')
        if not done:
            return ServerError()
        return True
    else:
        return InstructBusy()


def __execute_action_show_sys():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_action_show(form.para1.data, num=0, speed=form.para2.data)
    gl.set_value('state', 'WAITING')
    return True


def __execute_action_show_user():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_action_show(form.para1.data, num=1, speed=form.para2.data)
    gl.set_value('state', 'WAITING')
    return True


def __execute_code_show_sys():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_code_show(form.para1.data, 0)
    gl.set_value('state', 'WAITING')
    return True


def __execute_code_show_user():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_code_show(form.para1.data, 1)
    gl.set_value('state', 'WAITING')
    return True


def __execute_voice():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_voice(form.para1.data)
    gl.set_value('state', 'WAITING')
    return True


# By YJY
def __execute_show_code_frame():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_show_code_frame(form.para1.data)
    gl.set_value('state', 'WAITING')
    return True


def __execute_mode():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_mode(form.para1.data, form.para2.data)
    gl.set_value('state', 'WAITING')
    return True


def __execute_angle():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    Instruct.execute_angle(form.para1.data, form.para2.data)
    gl.set_value('state', 'WAITING')
    return True


def __execute_demarcate():
    gl.set_value('state', 'BUSY')
    form = InstructForm().validate_for_api()
    if Instruct.execute_demarcate(form.para2.data):
        gl.set_value('state', 'WAITING')
        return True
    else:
        gl.set_value('state', 'WAITING')
        return False
