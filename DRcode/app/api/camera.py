# coding=utf-8
import threading
from flask import jsonify

from DRcode.app.libs.redprint import Redprint
from DRcode.app.libs.error_code import Success, ServerError, InstructFailed
from DRcode.app.config.secure import CAMERA_PORT
import DRcode.app.libs.global_var as gl
from DRcode.app.libs.camera import Camera_TCP

# 实例化一个tcp连接
TCP = Camera_TCP(CAMERA_PORT)
api = Redprint('camera')


def camera_receiver():
    # 监听10000端口，若连续接收到3次来自同一ip的TCP连接，则返回"OK"
    if TCP.receive_message():
        gl.set_value('camera_connecting', False)
        return True
    else:
        return False


def camera_connection(ssid, passphrase):
    # 2摄像头TCP部分：建立TCP连接，监听端口获取摄像头IP地址
    while gl.get_value('camera_connecting'):
        t2 = threading.Thread(target=camera_receiver, name='TCP')
        t2.start()
        # 1摄像头UDP部分：UDP广播SSID和密码给摄像头配网
        from DRcode.app.libs.camera import Camera_UDP
        SENDERPORT = 45725
        if Camera_UDP(SENDERPORT).send_message(ssid, passphrase):
            return True
        else:
            return False


# 关闭摄像头
@api.route('/close', methods=['GET'])
def turn_off():
    from DRcode.app.libs.camera import Camera
    try:
        Camera().close_camera()
        gl.set_value('camera_open', False)
        return Success(msg='close camera successfully')
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))


# 摄像头配网
@api.route('', methods=['GET'])
def add_camera():
    try:
        from DRcode.app.libs.camera import Camera
        camera = Camera()
        # 如果摄像头已经处于打开状态，即摄像头处于网络配置成功阶段，直接返回摄像头IP地址
        if camera.get_camera_state():
            gl.set_value('camera_open', True)
            print('camera already turned on')
            ip_str = TCP.get_camera_ip()
            print('camera connectiong ip', ip_str)
            camera_ip = {"camera_ip": ip_str}
            return jsonify(camera_ip), 200
        # 否则打开摄像头、配网并返回IP地址
        else:
            print('turn on the camera')
            camera.start_camera()
            if not camera.get_camera_state():
                print('can not turn on the camera')
                return InstructFailed(msg='failed to turn on the camera')
            else:
                gl.set_value('camera_open', True)
                gl.set_value('camera_connecting', True)
                # 给摄像头配网
                print('add network for camera')
                from DRcode.app.libs.robot import Robot
                robot = Robot()
                ssid = robot.ssid
                wifi_password = robot.wifi_password

                # 向上位机返回摄像头IP地址
                if camera_connection(ssid, wifi_password):
                    ip_str = str(gl.get_value('camera_ip'), 'utf-8')
                    print('camera connectiong ip', ip_str)
                    camera_ip = {"camera_ip": ip_str}
                    return jsonify(camera_ip), 200
                else:
                    return InstructFailed(msg='failed to get camera id')
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))


