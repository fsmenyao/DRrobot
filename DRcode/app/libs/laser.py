import serial
import math as cm
import time

uart = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)


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
    time.sleep(0.1)
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


def get_distance(id_num):
    data = [0, 0, 13, 50, 0, 1, 0, 0]
    data[0] = 123
    data[1] = id_num
    # 下面两句话用来防止舵机运动到极限位置外，目前不支持负角度
    data[2] = 0x10
    data[3] = 0x10
    data[4] = 0
    data[5] = 0
    data[6] = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
    data[7] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    data = byte_list
    print(byte_list)
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id_number = byte_list[1]
            dis = byte_list[2] * 100 + byte_list[3]
            if dis == 4095:
                print("传感器读取数据有误，请重试一次")
                return False
            return dis

        else:
            print("返回的数据校验失败")
            return False
    else:
        print("返回的数据位数不够!")
        return False


def set_id(id_num=0, id_new=1):
    data = [0, 0, 0, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id_num
    data[2] = 0x10
    data[3] = 0x11
    data[4] = id_new
    data[5] = 0
    data[6] = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
    data[7] = 125
    write_data(data)

