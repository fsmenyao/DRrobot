from flask import jsonify
from DRcode.app.libs.redprint import Redprint
from DRcode.app.libs.error_code import Success, ServerError, InstructFailed
import threading
from DRcode.app.config.secure import CAMERA_PORT
import DRcode.app.libs.global_var as gl

api = Redprint('camera')


def camera_receiver():
    from DRcode.app.libs.camera import Camera_TCP
    # 监听10000端口，若连续接收到3次来自同一ip的TCP连接，则返回"OK"
    if Camera_TCP(CAMERA_PORT).receive_message():
        gl.set_value('camera_connecting', False)


def camera_connection(ssid, passphrase):
    while gl.get_value('camera_connecting'):
        # 2摄像头TCP部分：建立TCP连接，获取摄像头IP地址
        t2 = threading.Thread(target=camera_receiver, name='UDP')
        t2.start()
        # 1摄像头UDP部分：UDP广播SSID和密码给摄像头配网
        from DRcode.app.libs.camera import Camera_UDP
        SENDERPORT = 45725
        if Camera_UDP(SENDERPORT).send_message(ssid, passphrase):
            return True
        else:
            return False


# 添加摄像头
@api.route('', methods=['GET'])
def add_camera():
    try:
        # 打开摄像头
        from DRcode.app.libs.camera import Camera
        Camera().start_camera()
        gl.set_value('camera_open', True)
        gl.set_value('camera_connecting', True)
        # 给摄像头配网
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


@api.route('/close', methods=['GET'])
def close_camera():
    from DRcode.app.libs.camera import Camera
    try:
        Camera().close_camera()
        gl.set_value('camera_open', False)
        return Success(msg='close camera successfully')
    except Exception as result:
        print('检测出异常{}'.format(result))
        return ServerError(msg='Error{}'.format(result))
