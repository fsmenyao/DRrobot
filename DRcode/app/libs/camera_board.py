# coding=utf-8

import serial
import math as cm
import time

uart = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)


"""
created by LiuCuicui  2018.8.16
摄像头转接板

初始化波特率为19200  在writedata函数中将波特率修改为了115200
在每个函数结束后 将波特率重新初始化为19200


modified by Zhao Tang 2018.10.22
1.修改baudrate_init()函数，波特率可调；修改write_data函数，尽可能与舵机库保持一致；增加read_data函数。
2.修改其他函数名字，尽量保证通过名字知道函数功能。
3.采用read_data()函数改写需要返回数据的函数。


电量显示开关板t
turn_off()     //一个机器人上只有一个摄像头转接板，关闭摄像头，断掉摄像头电源
turn_on()      // 打开摄像头，给摄像头通电
"""


def baudrate_init(baud=19200):
    uart.baudrate = baud


def write_data(data=[], r_n=0):
    baudrate_init(115200)
    check = 0
    num = len(data)
    if num >= 2:
        data[num - 2] = 0
        for i in range(num - 2):
            check += data[i + 1]
        data[num - 2] = check % 100
        uart.write(data)
    else:
        print("待发送的数据有误！")
    if r_n == 0:  # 如果不需要接收数据，则直接恢复默认串口总线波特率
        baudrate_init()


def read_data(num=16):
    i = 100  # 经过测试，发现正常接收16位耗时大概为500，这里设置1000用来保证数据接收完成
    byte_list = []
    n_s = True
    while uart.inWaiting() < num and i > 0:  # To do:
        i -= 1
        if uart.inWaiting() > 0 and n_s:
            if list(uart.read(1))[0] == 123:
                n_s = False
                byte_list.append(123)
    while uart.inWaiting() > 0:
        byte_list.append(list(uart.read(1))[0])
    if len(byte_list) == num:
        baudrate_init()
        return byte_list
    else:
        print("接收的数据有误:")
        print(byte_list)
        baudrate_init()
        return []


def turn_on(state=0):
    """function:
    摄像头转接板
    控制摄像头开机上电
    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x30
    data[3] = 0x13
    data[4] = 0x01
    data[5] = 0
    data[7] = 125
    write_data(data)


def turn_off(state=0):
    """function:
    摄像头转接板
    控制摄像头关机断电
    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x30
    data[3] = 0x13
    data[4] = 0x00
    data[5] = 0
    data[7] = 125
    write_data(data)


def get_camera_state():
    """function:
    摄像头转接板
    获取摄像头电源状态
    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x30
    data[3] = 0x14
    data[4] = 0
    data[5] = 0
    data[6] = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    # print(byte_list)
    if len(byte_list) == 8:
        check = (byte_list[1] + byte_list[2] + byte_list[3] + byte_list[4] + byte_list[5]) % 100
        if byte_list[6] == check and byte_list[0] == 123:
            if byte_list[4] == 1:
                return True
            elif byte_list[4] == 0:
                return False
        else:
            print("返回的数据校验失败")
            return False
    else:
        print("读取摄像头开关状态失败")
        return False
