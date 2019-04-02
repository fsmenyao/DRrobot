#! /usr/local/bin/python3
# -*- coding: utf-8 -*-
from DRcode.app import create_app, create_global_var, check_ps
import threading
from DRcode.app.config.secure import UDP_PORT, APP_UDP_PORT, APP_UDP_IP
from DRcode.app.libs.robot import Robot


def udp():
    # from DRcode.app.libs.robot import Robot
    Robot().udp_connect(UDP_PORT)


def app_udp():
    # from DRcode.app.libs.robot import Robot
    Robot.app_udp_connect()


def sensors():
    Robot.robot_sensors()


t1 = threading.Thread(target=udp, name='UDP')
t2 = threading.Thread(target=app_udp, name='APP_UDP')
t3 = threading.Thread(target=sensors, name='sensors')

app = create_app()
create_global_var()
check_ps()

if __name__ == '__main__':
    # UDP连接：监听8080端口，若接收到本机机器人代号则返回ip地址
    t1.start()
    t2.start()
    # t3.start()
    # 启动flask监听5000端口
    app.run(host='0.0.0.0', port=5000, threaded=True)
