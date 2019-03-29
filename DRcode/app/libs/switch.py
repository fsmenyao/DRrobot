import serial
import math as cm
import time

uart = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)

"""
created by MrWang  2018.10.16
电量显示开关板

初始化波特率为19200  在writedata函数中将波特率修改为了15200
在每个函数结束后 将波特率重新初始化为19200


modified by Zhao Tang 2018.10.22
1.修改baudrate_init()函数，波特率可调；修改write_data函数，尽可能与舵机库保持一致；增加read_data函数。
2.修改其他函数名字，尽量保证通过名字知道函数功能。
3.采用read_data()函数改写需要返回数据的函数。


电量显示开关板函数
shut_down(state=0)     //无需ID  一个机器人上只有一个电量显示板
set_mode(state=1)      //state 取值范围1-3  表示三种闪烁样式
get_voltage()        //返回当前电池电压及电量值

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


def shut_down(state=0):
    """function:
    开关灯板
    控制机器人电源开断

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x20
    data[3] = 0x10
    if state == 0:
        data[4] = 0x00
    elif state == 1:
        data[4] = 0x01
    data[5] = 0
    data[7] = 125
    write_data(data)


def set_mode(state=1):
    """function:
    电量显示模块LED灯控制
    state：  取值范围1-3
    4个LED不同的闪烁样式

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x20
    data[3] = 0x12
    data[4] = state
    data[5] = 0
    data[7] = 125
    write_data(data)


def get_voltage():
    """function:
    电量显示模块
    读取当前电池电压及电量
    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = 0
    data[2] = 0x20
    data[3] = 0x11
    data[4] = 0
    data[5] = 0
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    # print(byte_list)
    if len(byte_list) == 8:
        check = (byte_list[1] + byte_list[2] + byte_list[3] + byte_list[4] + byte_list[5]) % 100
        if byte_list[6] == check and byte_list[0] == 123:
            board_type = byte_list[1]
            volt = byte_list[2] + byte_list[3] / 100
            energy = byte_list[4] * 100 + byte_list[5]
            # print("电池电压为", volt, "v")
            return energy
        else:
            print("返回的数据校验失败")
            return False
    else:
        print("读取电量失败")
        return False
