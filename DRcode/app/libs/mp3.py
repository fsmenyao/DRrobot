#!/usr/bin/python3
import time
import serial

# 端口初始化，总线初始化
sensor = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)


def write_data(data=[]):
    # print(data)
    sensor = serial.Serial('/dev/ttyAMA0', 9600, timeout=0.1)
    sensor.write(data)
    sensor = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)


def select_dir_song(num1=0x00, num2=0x02):  # 指定文件夹曲目播放（00-99/1-255�?
    if 0 <= num1 <= 99:
        if 1 <= num2 <= 255:
            data = [0x7E, 0x05, 0x42, 0x00, 0x02, 0x45, 0xEF]
            data[3] = num1
            data[4] = num2
            data[5] = data[1] ^ data[2] ^ data[3] ^ data[4]
            # print(data)
            write_data(data=data)


def spots_dir_song(num1=0x01, num2=0x06):  # 插播指定文件夹曲目（00-99/1-255�?
    if 0 <= num1 <= 99:
        if 1 <= num2 <= 255:
            data = [0x7E, 0x05, 0x42, 0x01, 0x06, 0x46, 0xEF]
            data[3] = num1
            data[4] = num2
            data[5] = data[1] ^ data[2] ^ data[3] ^ data[4]
            # print(data)
            write_data(data=data)


def insert_song(num1=0x01, num2=0xFE):  # 插播指定文件夹曲目（00-99/1-255�?
    if 0 <= num1 <= 99:
        if 1 <= num2 <= 255:
            data = [0x7E, 0x05, 0x43, 0x01, 0x06, 0x46, 0xEF]
            data[3] = num1
            data[4] = num2
            data[5] = data[1] ^ data[2] ^ data[3] ^ data[4]
            # print(data)
            write_data(data=data)


def stop():  # 停止
    data = [0x7E, 0x03, 0x0E, 0x0D, 0xEF]
    write_data(data=data)


def change_dev(num=0x01):  # 设备切换�?（U盘）�?（SD�?
    if num == 0 or num == 1:
        data = [0x7E, 0x04, 0x35, 0x01, 0x30, 0xEF]
        data[3] = num
        data[4] = data[1] ^ data[2] ^ data[3]
        # print(data)
        write_data(data=data)


def set_cmode(cmode=0x04):  # 设置循环模式�?-4(全盘/文件�?单曲/随机/无循�?
    if 0 <= cmode <= 4:
        data = [0x7E, 0x04, 0x33, 0x02, 0x35, 0xEF]
        data[3] = cmode
        data[4] = data[1] ^ data[2] ^ data[3]
        # print(data)
        write_data(data=data)


def set_vol(vol=0x1d):  # 设置音量�?-30�?
    if 0 <= vol <= 30:
        data = [0x7E, 0x04, 0x31, 0x19, 0x2C, 0xEF]
        data[3] = vol
        data[4] = data[1] ^ data[2] ^ data[3]
        # print(data)
        write_data(data=data)


def get_mode():
    data = [0x7E, 0x03, 0x01, 0x2C, 0xEF]
    data[3] = data[1] ^ data[2]
    # print(data)
    write_data(data=data)

