

import serial
import math as cm
import time

uart = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)


"""
created by liucuicui  2019.1.26
触摸传感器板 库

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


def get_touch(id_num=0):
    """
    读取当前触摸状态
    :param
        id_num: 要读取的触摸传感器的编号
    :return
        返回触摸传感器三个区域的触摸状态 1 表示当前正在触摸  0 表示当前没有触摸

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x10
    data[4] = 0
    data[5] = 0
    data[6] = 0
    # data[6] = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(9)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 9:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5] + data[6]) % 100
        if byte_list[7] == ca and byte_list[0] == 123:
            id_num = byte_list[1]
            board_type = byte_list[2]
            cmd = byte_list[3]
            touch1 = byte_list[4]
            touch2 = byte_list[5]
            touch3 = byte_list[6]
            if board_type == 0x60:
                print("id号为" + str(id_num) + "的触摸传感器的状态为:" + str(touch1) + "," + str(touch2) + "," + str(touch3))
            return [touch1, touch2, touch3]
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False


def get_gesture(id_num=0):
    """
    读取当前手势
    :param
        id_num: 要读取的触摸传感器的编号
    :return
        返回手势号
            17 （0x11）：表示触摸了同一块区域
            17 （0x12）：表示触摸了同一块区域
            17 （0x11）：表示触摸了同一块区域
            17 （0x11）：表示触摸了同一块区域

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x30
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(9)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 7:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5] + data[6]) % 100
        if byte_list[7] == ca and byte_list[0] == 123:
            id_num = byte_list[1]
            board_type = byte_list[2]
            cmd = byte_list[3]
            gesture = byte_list[5]
            print("手势为" + str(gesture))
            return gesture
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False


def get_speed(id_num=0):
    """
    :param id_num:
    :return:
    """
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x31
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(9)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 7:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5] + data[6]) % 100
        if byte_list[7] == ca and byte_list[0] == 123:
            id_num = byte_list[1]
            board_type = byte_list[2]
            cmd = byte_list[3]
            speed = byte_list[5]*255+byte_list[6]
            print("速度为" + str(speed) + "ms")
            return speed
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False


def set_id(id_num=0, id_new=1):
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x20
    data[4] = id_new
    data[5] = 0
    data[6] = 0
    data[7] = 125
    write_data(data)


def read_flash(id_num=0, flash_addr=1):
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x40
    data[4] = flash_addr
    data[5] = 0
    data[6] = 0
    # data[6] = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(7)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 7:
        ca = (data[1] + data[2] + data[3] + data[4]) % 100
        if byte_list[5] == ca and byte_list[0] == 123:
            id_num = byte_list[1]
            board_type = byte_list[2]
            cmd = byte_list[3]
            flash_data = byte_list[4]
            items_value = ['ID号', '硬件版本', '软件版本']
            print(items_value[flash_addr-1] + "为" + str(flash_data))
            return flash_data
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False


def write_flash(id_num=0, flash_addr=1, flash_data=1):
    """目前只存了地址"""
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x50
    data[4] = flash_addr
    data[5] = flash_data
    data[6] = 0
    data[7] = 125
    write_data(data)


def flash_init(id_num=0):
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x60
    data[3] = 0x51
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 125
    write_data(data)




