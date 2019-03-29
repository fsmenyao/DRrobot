# -*- coding: utf-8 -*-
import os
import time
import subprocess
from DRcode.app.config.secure import ROBOT_ID, APP_DATA, APP_UDP_PORT, APP_UDP_IP
from DRcode.app.config.setting import ACTION_PATH_USER
from DRcode.app.config.setting import CODE_PATH_USER
from DRcode.app.config.setting import ACTION_PATH_SYS
from DRcode.app.config.setting import CODE_PATH_SYS
from DRcode.app.config.setting import WIFI_PATH
from DRcode.app.libs.error_code import NotFound, InstructFailed, Success, ServerError, ParameterException
from DRcode.app.libs.meta_robot import MetaRobot, APP_UDP_S
import DRcode.app.libs.global_var as gl
import socket

import operator
import threading
from DRcode.app.libs import servo_rpi as se
from DRcode.app.libs import music as mp

# from DRcode.app.libs import udp as u

# 装配机器人初始模型角度
ID_LIST = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
P1_LIST = [1, 1, -1, 1, 1, -1, 1, 1, -1, 1, 1, -1, 1, -1, 1, 1, 1]
model_angle = [0, -21.8, 21.8, 0, -21.8, 21.8, 0, -21.8, 21.8, 0, -21.8, 21.8, 90, 90, 180, 180,
               180]
origaker = MetaRobot(ID_list_temp=ID_LIST, P1_list_temp=P1_LIST, init_model_angle_temp=model_angle)

hn = 0
sn = 0
zn = 0
xn = 0

flag = 1


def process_ip(content):
    try:
        index1 = content.find('=')
        robot_ip = content[index1 + 1:]
        return robot_ip.strip()
    except Exception:
        raise


def process_ssid(content):
    try:
        index1 = content.find("=")
        ssid = content[index1 + 1:]
        return ssid
    except Exception:
        raise


def process_ssid_list(content):
    try:
        contents = content.split('SSID:')[1:]
        contents = [content.replace('\n', '') for content in contents]
        contents = [content.replace('\"', '') for content in contents]
        ssid_list = [content.strip() for content in contents]
        return ssid_list
    except Exception:
        raise


def process_bssid(content):
    try:
        index1 = content.find("=")
        bssid = content[index1 + 1:]
        bssid_list = []
        bssid_dec = [('0x' + num[0:4].strip()) for num in bssid.split(':')]
        bssid_list.append(':'.join(bssid_dec))
        return bssid_list[0]
    except Exception:
        raise


def process_net_id(content):
    try:
        index1 = content.find('=')
        robot_net_id = content[index1 + 1:]
        return robot_net_id.strip()
    except Exception:
        raise


def process_wifi_password(content):
    try:
        index1 = content.find('psk=')
        content = content[index1 + 5:]
        index2 = content.find('"')
        robot_wifi_password = content[:index2]
        return robot_wifi_password.strip()
    except Exception:
        raise


def process_list_network(content):
    import re
    list_ssid = []
    list_netid = []
    netlist = re.findall('(.*)any.*\n', content)
    for item in netlist:
        ssid = re.findall('\t(.*)\t', item)
        netid = re.findall('(\d?)\s', item)
        list_ssid.append(ssid[0])
        list_netid.append(netid[0])
    return list_ssid, list_netid


def get_net_id():
    try:
        instruct_get_id = "sudo wpa_cli -i wlan0 status | grep ^\'id\'"
        # print(instruct_get_id)
        get_id = os.popen(instruct_get_id).read()
        # print('get id', get_id)
        net_id = process_net_id(get_id)
        return net_id
    except Exception as result:
        print('检测出异常{} in /robot/get_net_id'.format(result))
        raise


def get_net_ssid():
    try:
        ssid = os.popen('sudo wpa_cli -i wlan0 status|grep ^\"ssid\"').read()
        # print('get id', get_id)
        print("当前连接网络为：" + ssid)
        mp.speak("当前连接网络为：" + ssid)
    except Exception as result:
        print('检测出异常{} in /robot/get_net_ssid'.format(result))


def delete_network(net_id):
    print('delete netid', net_id)
    instruct_delete_net = 'sudo wpa_cli -i wlan0 remove_network ' + net_id
    os.system(instruct_delete_net)


def change_priority(high_id, low_id):
    # print('change priority---------------')
    instruct_priority_list = [
        "sudo wpa_cli -i wlan0 set_network " + high_id + " priority \'2\'",
        "sudo wpa_cli -i wlan0 set_network " + low_id + " priority \'1\'",
        "sudo wpa_cli -i wlan0 enable_network " + high_id,
        "sudo wpa_cli -i wlan0 enable_network " + low_id,
        "sudo wpa_cli -i wlan0 save_config"
    ]
    try:
        for i, instruct in enumerate(instruct_priority_list):
            os.system(instruct)
    except Exception as result:
        print('检测出异常{} in /robot/change_priority'.format(result))
        raise


def restart_wifi():
    # print('restart wifi--------------------')
    instruct_restart = ["sudo systemctl restart networking",
                        "sudo ip link set wlan0 down",
                        "sudo ip link set wlan0 up"]
    try:
        for item in instruct_restart:
            os.system(item)
        time.sleep(10)
    except Exception:
        raise


# 检查序号为net_id的网络是否能成功连接
def check_wifi_config(org_id, net_id):
    try:
        change_priority(net_id, org_id)
        restart_wifi()
        new_id = get_net_id()
        # 如果new_id与我们希望连接的net_id号一致则连接成功
        if new_id == net_id:
            return True
        else:
            return False
    except Exception as result:
        print('检测出异常{} in /robot/check_wifi_config'.format(result))
        return False


def write_action(action_name, action_body, path='usr'):
    try:
        if path == 'sys':
            file_path = ACTION_PATH_SYS + action_name + '.txt'
        else:
            file_path = ACTION_PATH_USER + action_name + '.txt'
        fd = open(file_path, 'w+')
        fd.write(action_body)
    except Exception as result:
        print('检测出异常{} in /robot/write_action'.format(result))
        raise
    finally:
        fd.close()


def write_code(code_name, code_body):
    try:
        file_path = CODE_PATH_USER + code_name + '.py'
        fd = open(file_path, "w+")
        fd.write(code_body)
        os.system('sudo chmod 777' + file_path)  # 改变文件权限，保证可以执行
    except Exception as result:
        print('检测出异常{} in /robot/write_code'.format(result))
        raise
    finally:
        fd.close()


def get_file_list(path):
    try:
        instruct = 'ls ' + path
        return os.popen(instruct).read().split('\n')[:-1]
    except Exception:
        raise


def get_num_of_nets():
    list_network = os.popen('sudo wpa_cli -i wlan0 list_network').read()
    nets = len(list_network.split('\n')) - 2
    return nets


def receive_data(level=0, data=[]):
    byte_list = []
    n_s = True
    data_len = len(data)
    a = 0
    # i = 2000  # 经过测试，发现正常接收16位耗时大概为500，这里设置1000用来保证数据接收完成
    if level == 1:
        i = 1
        # print("run_order:")
    else:
        pass
        # print("main:")
    while n_s and a < data_len:
        byte = data[a]
        a = a + 1
        if level == 1:
            if byte != 123:
                print("动作执行中，run_order第一位不是0x7b,终止接收")
                return []
        if byte == 123:
            n_s = False
            byte_list.append(123)
        elif byte == 35:
            # print("ok")
            n_s = False
            byte_list.append(35)
        elif byte == 111 or byte == 107:
            print("O or K")
            return []
        else:
            pass
            # print(byte)
    while a < data_len and not n_s:
        byte = data[a]
        a = a + 1
        if byte != 125:
            byte_list.append(byte)
        else:
            byte_list.append(125)
            return byte_list
        if byte_list[0] == 35 and len(byte_list) == 4:
            if not (byte_list[2] == 71 or byte_list[3] == 71):
                if a < data_len:
                    byte = data[a]
                    a = a + 1
                    if byte == 71:
                        byte_list.append(byte)
                    else:
                        byte_list = []
                        n_s = True
                        print("out")
                        if len(byte_list) > 0:
                            print("接收到的数据出错：" + str(byte_list))
                else:
                    byte_list = []
                    n_s = True
                    print("out")
                    if len(byte_list) > 0:
                        print("接收到的数据出错：" + str(byte_list))
    return []


def analyze_data(data_temp=[]):
    # print(data_temp)
    id_list = []
    angle_list = []
    result = []
    i = 0
    if len(data_temp) > 0:
        if data_temp[i] == 123:
            result = []
            for element in data_temp:
                result.append(element)
                if element == 125:
                    return result
            print("接收到的数据出错：结尾符丢失。")
            return []
        while i < len(data_temp):
            if data_temp[i] == 35:
                num_list = []
                i += 1
                while data_temp[i] >= 48 and data_temp[i] <= 57:
                    num_list.append(data_temp[i])
                    i += 1
                if data_temp[i] == 71:
                    id_list.append(list_to_number(num_list))
            elif data_temp[i] == 67:
                num_list = []
                i += 1
                while data_temp[i] >= 48 and data_temp[i] <= 57:
                    num_list.append(data_temp[i])
                    i += 1
                time = list_to_number(num_list)
                result = [id_list, time]
            else:
                i += 1
        # print("analyze_data:", result)
        return result
    else:
        return []


def list_to_number(num_list=[]):
    number = 0
    for i in range(len(num_list)):
        if num_list[i] >= 48 and num_list[i] <= 57:
            number += (num_list[i] - 48) * (10 ** (len(num_list) - i - 1))
        else:
            print("the char is not a number in list_tu_number!")
            return False
    return number


def exe_cmd(cmd_list_temp=[], speed=1.0, app_socket=socket.socket(), addr=(APP_UDP_IP, APP_UDP_PORT)):
    global flag
    if len(cmd_list_temp) == 2:
        if flag:
            for i in range(cmd_list_temp[1]):
                for j in range(len(cmd_list_temp[0])):
                    exe_motion(cmd_list_temp[0][j], speed=speed, app_socket=app_socket, addr=addr)
    elif len(cmd_list_temp) == 4:
        if cmd_list_temp[1] == 0xaa and cmd_list_temp[2] == 0x55:
            print("收到手机app发来的四位数据：0x7b 0xaa 0x55 0x7d")
            # vol = MetaRobot().get_electricity()#se.show_voltage(1)
            # if(vol == None):
            vol = origaker.get_electricity()
            if vol != False:
                data = [0x7d, 0x06, 0x01, 0x64, 0x62, vol]
                # response = []
                # for msg in data:
                #     response.append(chr(msg))
                #     # response = chr(msg)
                # app_socket.sendto(bytes(''.join(response), 'utf-8'), addr)
                app_socket.sendto(bytes(data), addr)
                print("向手机app返回数据：0x7d 0x06 0x01 0x64 0x62 " + str(vol))
        if cmd_list_temp[1] == 0xaa and cmd_list_temp[2] == 0x66:
            print("收到手机app发来的四位数据：0x7b 0xaa 0x66 0x7d")
            c_state = origaker.get_state(2)
            if c_state > 0:
                data = [0x7d, 0x03, c_state]
                # response = []
                # for msg in data:
                #     response.append(chr(msg))
                #     # response = chr(msg)
                # app_socket.sendto(bytes(''.join(response), 'utf-8'), addr)
                app_socket.sendto(bytes(data), addr)
                print("向手机app发送机器人状态：" + str(c_state))
            else:
                print("获取机器人状态失败")
                origaker.say("获取机器人状态失败")
    elif len(cmd_list_temp) == 5:
        if cmd_list_temp[1] == 115 and cmd_list_temp[2] == 116 and cmd_list_temp[3] == 111:
            print("动作急停 flag=" + str(flag) + "state=" + str(gl.get_value('state')))
            if flag == 0:
                gl.set_value('state', 'STOP')
            else:
                origaker.set_joint_mode(121, "free")
            robot = Robot()
            robot.stop_music()
            flag = 1
            return True
    else:
        if len(cmd_list_temp) > 0:
            print("指令有误，无法识别！")
            print(cmd_list_temp)
        return False


def exe_motion(motion_number=1, time0=1, speed=1.0, app_socket=socket.socket(), addr=(APP_UDP_IP, APP_UDP_PORT)):
    global hn
    global sn
    global zn
    global xn
    global flag
    flag = 0
    # print(motion_number)
    if sn != 0 and origaker.c_state == 4:
        origaker.exe_action(action_name='sit_up', speed=0.3 * speed, path='sys')
        sn = 0
    for i in range(time0):
        if motion_number == 2:
            origaker.exe_action(action_name='to_spider1', speed=0.5 * speed, path='sys')
        elif motion_number == 3:
            origaker.exe_action(action_name='to_spider2', speed=1 * speed, path='sys')
        elif motion_number == 4:
            origaker.exe_action(action_name='to_stick2', speed=0.5 * speed, path='sys')
        elif motion_number == 5:
            origaker.exe_action(action_name='transform', speed=0.3 * speed, path='sys')
            origaker.exe_action(action_name='to_dog1', speed=0.5 * speed, path='sys')
        elif motion_number == 6:
            se.set_mode(121, 3)
        elif motion_number == 7:
            origaker.exe_action(action_name='pack', speed=0.5 * speed, path='sys')
        elif motion_number == 10:
            # if sn == 0 and origaker.c_state != 1:
            origaker.exe_action(action_name='to_spider1', speed=0.5 * speed, path='sys')  # 壁虎
        elif motion_number == 11:
            origaker.exe_action(action_name='go_forward', speed=1 * speed, path='sys')
        elif motion_number == 12:
            origaker.exe_action(action_name='go_back', speed=1 * speed, path='sys')
        elif motion_number == 13:
            origaker.exe_action(action_name='turn_left2', speed=1 * speed, path='sys')
        elif motion_number == 14:
            origaker.exe_action(action_name='turn_right2', speed=1 * speed, path='sys')
        elif motion_number == 15:
            origaker.exe_action(action_name='opening', speed=1 * speed, path='sys')
        elif motion_number == 16:
            origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
        elif motion_number == 17:
            origaker.exe_action(action_name='pack', speed=0.5 * speed, path='sys')
            se.set_mode(121, 3)
        elif motion_number == 1:
            origaker.exe_action(action_name='unpack', speed=1.0 * speed, path='sys')
        elif motion_number == 18 or motion_number == 131:  # 舞蹈4----海草舞
            if motion_number == 131:
                motions = [['spots_dir_song', 220], ['delay', 6800], ['spots_dir_song', 210]]
                origaker.zip_action(order=motions)
            else:
                time.sleep(5)
            motions = [['dance1', 0.7], ['rot_body', 0.7], ['turn_right', 0.8], ['dance3', 0.7],
                       ['turn_left', 0.8], ['dance1', 0.7], ['rectangle', 0.3], ['dance3', 0.7],
                       ['deform_body', 0.4], ['dance4', 0.7], ['stick_trunk', 0.3],
                       ['triangle', 0.3], ['dance2', 0.7], ['dance4', 0.7], ['trans_body', 0.3],
                       ['spider_shake', 0.5], ['to_spider2', 0.5], ['spots_dir_song', 254], ['delay', 100],
                       ['spots_dir_song', 47]]
            origaker.zip_action(order=motions)
        elif motion_number == 19:
            origaker.exe_action(action_name='transform', speed=0.3 * speed, path='sys')
        elif motion_number == 20:
            origaker.exe_action(action_name='to_spider2', speed=0.5 * speed, path='sys')  # 蜘蛛
        elif motion_number == 21:
            origaker.exe_action(action_name='crab_forward', speed=1 * speed, path='sys')
        elif motion_number == 22:
            origaker.exe_action(action_name='crab_backward', speed=1 * speed, path='sys')
        elif motion_number == 23:
            origaker.exe_action(action_name='turn_left', speed=1 * speed, path='sys')
        elif motion_number == 24:
            origaker.exe_action(action_name='turn_right', speed=speed, path='sys')
        elif motion_number == 25:
            origaker.exe_action(action_name='spider_shake', speed=0.5 * speed, path='sys')
        elif motion_number == 26:
            origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
        elif motion_number == 28 or motion_number == 132:  # 舞蹈6----可爱颂
            # if motion_number == 132:
            #     motions = [['spots_dir_song', 216], ['delay', 5000], ['spots_dir_song', 206]]
            #     origaker.zip_action(order=motions)
            # else:
            #     time.sleep(5)
            # motions = [['transform', 0.4], ['tabu', 0.3],
            #            ['serial_hand', 0.3], ['serial_dance', 0.3], ['serial_dance', 0.3], ['sit_up', 0.3],
            #            ['transform_back', 0.3], ['turn_right', 1.0], ['turn_right', 1.0], ['turn_right', 1.0],
            #            ['to_spider2', 0.5], ['spots_dir_song', 254], ['delay', 100], ['spots_dir_song', 47]]
            # origaker.zip_action(order=motions)
            print("舞蹈-青春修炼手册-74")
            motions = [['delay', 6800], ['gecko_yaohuang', 0.3], ['circle_right', 0.4], ['circle_left', 0.4],
                       ['delay', 200], ['to_gecko', 0.7], ['gecko_roll_body', 0.5],
                       ['delay', 500], ['trans_body', 0.3], ['turn_right', 0.8], ['turn_left', 0.8],
                       ['spider_change', 0.4], ['rectangle_1', 0.7], ['to_stick', 0.7],
                       ['stick_pa', 0.5],
                       ['to_stick', 0.7], ['stick_trunk', 0.5], ['stick_trunk', 0.5], ['stick_fuwocheng', 0.7],
                       ['stick_dian', 0.5], ['stick_right', 0.8], ['stick_right', 0.8], ['stick_right', 0.8],
                       ['to_stick', 0.7], ['stick_dian', 0.5], ['stick_dian2', 0.4],
                       ['out_box1', 0.5], ['dog_lash_tail', 0.5], ['dog_yaobai', 0.5], ['dog_baidong', 0.5],
                       ['dog_hands', 0.4], ['dog_circle_left', 0.3],
                       ['dog_circle_right', 0.3], ['triangle1', 0.7], ['turn_left', 0.8], ['turn_left', 0.8],
                       ['trans_body', 0.3], ['spider_shake_hand', 0.5], ['to_spider1', 0.7]]
            origaker.zip_action(order=motions)
            origaker.rotate_pitch(attitude="gecko", angle=15, speed=0.2)
            origaker.rotate_pitch(attitude="gecko", angle=0, speed=0.2)
        elif motion_number == 29:
            origaker.exe_action(action_name='transform', speed=0.3 * speed, path='sys')
        elif motion_number == 30:
            origaker.exe_action(action_name='to_stick2', speed=0.5 * speed, path='sys')  # 竹节虫
        elif motion_number == 31:
            origaker.exe_action(action_name='stick_forward', speed=1.0 * speed, path='sys')
        elif motion_number == 32:
            origaker.exe_action(action_name='stick_back', speed=1.0 * speed, path='sys')
        elif motion_number == 33:
            origaker.exe_action(action_name='stick_left', speed=0.5 * speed, path='sys')
        elif motion_number == 34:
            origaker.exe_action(action_name='stick_right', speed=0.5 * speed, path='sys')
        elif motion_number == 35:
            origaker.exe_action(action_name='stick_shake1', speed=0.5 * speed, path='sys')
        elif motion_number == 36:
            origaker.exe_action(action_name='roll_body', speed=0.5 * speed, path='sys')
            origaker.exe_action(action_name='to_stick1', speed=0.5 * speed, path='sys')
        elif motion_number == 37:
            # motions = [['to_stick1', 0.5], ['spots_dir_song', 60], ['stick_forward', 1.0], [
            #     'stick_forward', 1.0], ['stick_shake_body', 0.5], ['spots_dir_song', 61], ['delay', 1500], [
            #                'spots_dir_song', 62], ['stick_up3', 0.5], ['to_stick1', 0.5],
            #            ['spots_dir_song', 64], ['stick_shake1', 0.5], ['to_stick1', 0.3]]
            # origaker.zip_action(order=motions)
            origaker.spots_dir_song(1, 67)
            origaker.goto_shape(attitude="stick", speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=15, speed=0.3)
            origaker.rotate_roll(attitude="stick", angle=-15, speed=0.3)
            origaker.rotate_roll(attitude="stick", angle=15, speed=0.3)
            origaker.rotate_roll(attitude="stick", angle=-15, speed=0.3)
            origaker.rotate_roll(attitude="stick", angle=15, speed=0.3)
            origaker.rotate_roll(attitude="stick", angle=0, speed=0.1)
            origaker.spots_dir_song(1, 68)
            time.sleep(2)
            origaker.show_action(attitude="stick", action="go_upstairs", speed=0.5)
            origaker.show_action(attitude="stick", action="go_upstairs", speed=0.5)
            origaker.go_forward(attitude="stick", length=100, height=50, speed=0.3)
            origaker.spots_dir_song(1, 65)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.25)
            origaker.rotate_roll(attitude="stick", angle=15, speed=0.25)
        elif motion_number == 38:
            # motions = [['spots_dir_song', 65], ['stick_down1', 0.5], ['stick_back', 1.0], ['stick_back', 1.0],
            #            ['to_stick1', 0.5]]
            # origaker.zip_action(order=motions)
            origaker.goto_shape(attitude="spider", speed=0.5)
            origaker.box = 0
            origaker.spots_dir_song(1, 30)
            time.sleep(3)
            origaker.spots_dir_song(1, 31)
            origaker.rotate_pitch(attitude="spider", angle=15, speed=0.5)
            origaker.rotate_pitch(attitude="spider", angle=-15, speed=0.5)
            origaker.rotate_pitch(attitude="spider", angle=15, speed=0.5)
            origaker.rotate_pitch(attitude="spider", angle=-15, speed=0.5)
            origaker.spots_dir_song(1, 32)
            time.sleep(1.5)
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.zip_action(order=[['stick_forward2', 0.8]])
            origaker.goto_shape(attitude="spider", speed=0.5)
            origaker.spots_dir_song(1, 33)
        elif motion_number == 39:
            origaker.exe_action(action_name='transform', speed=0.3 * speed, path='sys')
        elif motion_number == 40:
            origaker.exe_action(action_name='to_dog1', speed=0.5 * speed, path='sys')  # 小狗
        elif motion_number == 41:
            origaker.exe_action(action_name='serial_forward', speed=1.0 * speed, path='sys')
        elif motion_number == 42:
            origaker.exe_action(action_name='serial_back', speed=1.0 * speed, path='sys')
        elif motion_number == 43:
            origaker.exe_action(action_name='serial_left', speed=1.0 * speed, path='sys')
        elif motion_number == 44:
            origaker.exe_action(action_name='serial_right', speed=1.0 * speed, path='sys')
        elif motion_number == 45:
            if hn == 0:
                origaker.exe_action(action_name='serial_hand', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_hand1', speed=0.5 * hn * speed, path='sys')
            hn = hn + 1
        elif motion_number == 46:
            origaker.exe_action(action_name='shake_head_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 47:
            origaker.exe_action(action_name='shake_tail_kay2', speed=0.7 * speed, path='sys')
        elif motion_number == 48:
            origaker.exe_action(action_name='sit_down', speed=0.5 * speed, path='sys')
            sn = 1
        elif motion_number == 49:
            origaker.exe_action(action_name='transform_back', speed=0.5 * speed, path='sys')
        elif motion_number == 50 or motion_number == 133:  # 舞蹈5----广播体操
            if motion_number == 133:
                motions = [['spots_dir_song', 218], ['delay', 5000], ['spots_dir_song', 208]]
                origaker.zip_action(order=motions)
            else:
                origaker.exe_action(action_name='to_spider1', speed=500 * speed)
                time.sleep(7.8)
            motions = [['to_spider1', 0.5], ['delay', 2000],
                       ['go_forward', 1.5], ['go_forward', 1.5], ['to_spider1', 0.5],
                       ['go_back', 1.4], ['go_back', 1.4], ['to_spider1', 0.5], ['delay', 1600],
                       ['delay', 1500],
                       ['to_stick1', 0.5], ['stick_forward', 0.7], ['roll_body', 0.7], ['to_stick1', 0.5],
                       ['delay', 1000],
                       ['to_stick1', 0.5], ['stick_back', 0.7], ['roll_body', 0.7], ['to_stick1', 0.5],
                       ['delay', 1900],
                       ['to_stick1', 0.5], ['stick_forward', 0.7], ['roll_body', 0.7], ['to_stick1', 0.5],
                       ['delay', 1200],
                       ['to_stick1', 0.5], ['stick_back', 0.7], ['roll_body', 0.7], ['to_stick1', 0.5],
                       ['delay', 3400],
                       ['to_spider2', 0.5], ['crab_forward', 1.2], ['trans_body', 0.5], ['to_spider2', 0.5],
                       ['crab_backward', 1.0], ['trans_body', 0.5], ['trans_body', 0.5], ['to_spider2', 0.5],
                       ['to_spider2', 0.5], ['crab_forward', 1.2], ['trans_body', 0.5], ['to_spider2', 0.5],
                       ['crab_backward', 1.0], ['trans_body', 0.5], ['trans_body', 0.5], ['to_spider2', 0.5],
                       ['delay', 500], ['spider_shake', 0.5], ['spots_dir_song', 254], ['delay', 100],
                       ['spots_dir_song', 47]]
            origaker.zip_action(order=motions)
        elif motion_number == 51:
            origaker.spots_dir_song(1, 1)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_forward', speed=0.5 * speed, path='sys')
        elif motion_number == 52:
            origaker.spots_dir_song(1, 2)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_left', speed=0.5 * speed, path='sys')
        elif motion_number == 53:
            origaker.spots_dir_song(1, 3)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='shake_tail_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 54:
            origaker.spots_dir_song(1, 4)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_forward', speed=0.5 * speed, path='sys')
        elif motion_number == 55:
            origaker.spots_dir_song(1, 5)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_forward', speed=0.5 * speed, path='sys')
        elif motion_number == 56:
            origaker.spots_dir_song(1, 6)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_back', speed=0.5 * speed, path='sys')
        elif motion_number == 57:
            origaker.spots_dir_song(1, 7)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_right', speed=0.5 * speed, path='sys')
        elif motion_number == 58:
            origaker.spots_dir_song(1, 8)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_left', speed=0.5 * speed, path='sys')
        elif motion_number == 59:
            origaker.spots_dir_song(1, 9)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='shake_tail_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 60:
            origaker.spots_dir_song(1, 10)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='shake_head_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 61:
            origaker.spots_dir_song(1, 11)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_forward', speed=0.5 * speed, path='sys')
                origaker.exe_action(action_name='serial_back', speed=0.5 * speed, path='sys')
        elif motion_number == 62:
            origaker.spots_dir_song(1, 12)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='shake_head_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 63:
            origaker.spots_dir_song(1, 13)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='rot_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='serial_forward', speed=0.5 * speed, path='sys')
        elif motion_number == 64:
            origaker.spots_dir_song(1, 14)
            if origaker.c_state != 4:
                origaker.exe_action(action_name='trans_body', speed=0.5 * speed, path='sys')
            else:
                origaker.exe_action(action_name='shake_head_kay2', speed=0.5 * speed, path='sys')
        elif motion_number == 70:  # 自我介绍
            # motions = [['spots_dir_song', 21], ['opening', 1.0], ['rot_body', 0.5],
            #            ['delay', 2500],
            #            ['spots_dir_song', 22], ['to_spider1', 1.0], ['run_forward2', 10], ['run_forward2', 10],
            #            ['turn_left2', 1.0], ['turn_left2', 1.0], ['turn_left2', 1.0], ['delay', 1000],
            #            ['spots_dir_song', 23],
            #            ['to_stick2', 1.0], ['delay', 4200], ['roll_body', 1.0], ['roll_body', 1.0],
            #            ['stick_shake1', 0.5], ['delay', 1000],
            #            ['spots_dir_song', 24], ['delay', 400], ['to_spider0', 0.5], ['delay', 1000],
            #            ['trans_body', 0.5],
            #            ['turn_right', 1.0], ['turn_right', 1.0], ['turn_right', 1.0], ['spider_shake', 0.5],
            #            ['spider_pack', 0.3],
            #            ['delay', 3000], ['spots_dir_song', 25], ['transform', 0.3], ['to_dog1', 0.5], ['delay', 500],
            #            ['spots_dir_song', 26], ['serial_forward', 1.0], ['delay', 100], ['spots_dir_song', 27],
            #            ['shake_head_kay2', 0.5],
            #            ['delay', 500], ['sit_down', 0.5], ['delay', 500], ['sit_up', 0.5],
            #            ['to_dog1', 0.5], ['delay', 2000], ['transform_back', 0.5],
            #            ['delay', 800], ['spots_dir_song', 28], ['delay', 500], ['to_spider1', 1.0]]
            # origaker.zip_action(order=motions)

            # 小狗
            origaker.goto_shape(attitude="dog", speed=0.5)
            origaker.spots_dir_song(1, 150)
            origaker.exe_action(action_name='serial_hand', speed=0.5 * speed, path='sys')
            origaker.goto_shape(attitude="dog", speed=0.5)
            time.sleep(5)
            origaker.spots_dir_song(1, 152)
            origaker.go_forward(attitude="dog", length=100, height=50, speed=0.5)
            origaker.go_forward(attitude="dog", length=100, height=50, speed=0.5)
            origaker.zip_action(order=[['spots_dir_song', 153], ['dog_nod_head', 0.4], ['dog_yaobai', 0.5],
                                       ['sit_down', 0.5],
                                       ['spots_dir_song', 154],
                                       ['dog_thanks', 0.4], ['spots_dir_song', 155], ['dog_rest', 0.2],
                                       ['delay', 1000], ['sit_up', 0.3], ['spots_dir_song', 156]])
            # 竹节虫
            origaker.goto_shape(attitude="stick", speed=0.5)
            origaker.spots_dir_song(1, 157)
            origaker.show_action(attitude="stick", action="arch_body", speed=0.5)
            origaker.show_action(attitude="stick", action="arch_body", speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_roll(attitude="stick", angle=-10, speed=0.5)
            time.sleep(0.5)
            origaker.rotate_pitch(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_pitch(attitude="stick", angle=-10, speed=0.5)
            origaker.rotate_pitch(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_pitch(attitude="stick", angle=-10, speed=0.5)
            origaker.rotate_pitch(attitude="stick", angle=10, speed=0.5)
            origaker.rotate_pitch(attitude="stick", angle=-10, speed=0.5)
            origaker.zip_action(order=[['spots_dir_song', 158], ['stick_fuwocheng', 0.6],
                                       ['stick_shake_body', 0.5], ['spots_dir_song', 159], ['stick_pa', 0.5]])
            # 蜘蛛
            time.sleep(1)
            origaker.spots_dir_song(1, 160)
            origaker.goto_shape(attitude="spider", speed=0.5)
            origaker.zip_action(order=[['spider_change', 0.5]])
            origaker.spots_dir_song(1, 161)
            for count in range(3):
                origaker.rotate_roll(attitude="spider", angle=10, speed=0.5)
                origaker.rotate_roll(attitude="spider", angle=-10, speed=0.5)
            for count2 in range(3):
                origaker.rotate_pitch(attitude="spider", angle=10, speed=0.5)
                origaker.rotate_pitch(attitude="spider", angle=-10, speed=0.5)
            origaker.exe_action(action_name="spider_pack", speed=0.5)
            time.sleep(1)
            origaker.show_action(attitude="spider", action="stand_toe", speed=0.5)
            origaker.spots_dir_song(1, 164)
            time.sleep(3)
            # 壁虎
            origaker.goto_shape(attitude="gecko", speed=0.5)
            origaker.spots_dir_song(1, 165)
            origaker.zip_action(
                order=[['gecko_roll_body', 0.5], ['gecko_unpack', 0.5], ['gecko_pack', 0.5],
                       ['gecko_unpack', 0.5], ['spots_dir_song', 167], ['gecko_go_forward0', 0.5],
                       ['gecko_go_forward0', 0.5]])
            origaker.goto_shape(attitude="gecko", speed=0.5)
            origaker.set_gecko_shape_twist(angle=20, speed=0.5)
            origaker.set_gecko_shape_twist(angle=-20, speed=0.5)
            origaker.spots_dir_song(1, 166)
            for count in range(2):
                origaker.set_gecko_shape_twist(angle=20, speed=0.5)
                origaker.set_gecko_shape_twist(angle=-20, speed=0.5)
            origaker.goto_shape(attitude="gecko", speed=0.5)
            origaker.exe_action('gecko_shake_hand1', 0.5)
            origaker.goto_shape(attitude="gecko", speed=0.5)
            origaker.spots_dir_song(1, 168)
        elif motion_number == 73:
            motions = [['transform_back', 0.3], ['to_stick1', 0.5], ['spots_dir_song', 60], ['stick_forward', 1.0], [
                'stick_forward', 1.0], ['stick_shake_body', 0.5], ['spots_dir_song', 61], ['delay', 1500], [
                           'spots_dir_song', 62], ['stick_up3', 0.5], ['to_stick1', 0.5], ['spots_dir_song', 64], [
                           'stick_shake1', 0.5], ['to_stick1', 0.3]]
            origaker.zip_action(order=motions)
        elif motion_number == 74:  # 相声----对对联
            origaker.exe_action(action_name='to_spider1', speed=500 * speed, path='sys')
            time.sleep(3)
            motions = [['spots_dir_song', 142], ['to_spider1', 0.5], ['delay', 8600],  # 是啊
                       ['spots_dir_song', 144], ['go_forward', 0.8], ['delay', 2200],  # 你的爱好是什么啊
                       ['spots_dir_song', 146], ['go_back', 0.5], ['delay', 1700],  # 啥是对联？
                       ['spots_dir_song', 148], ['to_spider1', 0.5], ['delay', 6800],  # 噢？是封条吧！
                       ['spots_dir_song', 150], ['rot_body', 0.5], ['delay', 4100],  # 哈哈，逗你的，就是过年门上贴的吉祥话呗
                       ['spots_dir_song', 152], ['trans_body', 0.5], ['delay', 7100],  # 光说不练假把式，咱们比试一下如何？
                       ['spots_dir_song', 154], ['go_forward', 0.7], ['delay', 5300],  # 我对，京北直通车通直北京
                       ['spots_dir_song', 156], ['go_back', 0.7], ['delay', 3400],  # 凤舞八方，方方保平安
                       ['spots_dir_song', 158], ['rot_body', 0.5], ['delay', 5400],  # 听我的上联：十口心思，思国思家思社稷
                       ['spots_dir_song', 160], ['to_spider2', 0.5], ['delay', 4600],  # 欲知后事如何
                       ['opening', 1.0], ['spots_dir_song', 162]]  # 谢谢大家
            origaker.zip_action(order=motions)
        elif motion_number == 75:  # 口令表演
            motions = [['to_spider1', 0.5], ['delay', 8000], ['delay', 1850],
                       ['trans_body', 0.6], ['to_spider2', 0.5], ['delay', 1900],
                       ['to_stick2', 2.5], ['roll_body', 0.5], ['to_stick2', 2.5], ['delay', 2400],
                       ['transform', 0.3], ['to_dog1', 0.5], ['delay', 2300],
                       ['dog_thanks', 0.5], ['spots_dir_song', 64], ['delay', 3000],
                       ['sit_up', 0.5], ['transform_back', 0.5], ['to_spider1', 0.5], ['turn_right2', 0.5],
                       ['turn_right2', 0.5], ['spots_dir_song', 253]]
            origaker.zip_action(order=motions)
        elif motion_number == 76:  # 开始变小狗
            motions = [['spots_dir_song', 132], ['delay', 200], ['transform', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 77:
            # origaker.exe_action(action_name='to_spider2', speed=0.5 * speed, path='sys')
            # origaker.exe_action(action_name='in_box', speed=0.3 * speed, path='sys')
            origaker.exe_action(action_name='dog_pack', speed=0.2 * speed, path='sys')
            origaker.say("机器人关机中。。。。")
            time.sleep(5)
            origaker.turn_off()
            flag = False
            while not flag:
                flag = exe_cmd(cmd_list_temp=analyze_data(receive_data()), speed=1.0)
                print(flag)
                time.sleep(1)
        elif motion_number == 78:
            origaker.exe_action(action_name='to_spider1', speed=500 * speed, path='sys')
            # origaker.exe_action(action_name='out_box', speed=0.3 * speed, path='sys')
        elif motion_number == 80:
            motions = [['go_forward', 1.0], ['go_forward', 2.5], ['to_spider1', 0.5], ['go_back', 1.0],
                       ['go_back', 2.5], ['to_spider1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 81:
            motions = [['to_spider1', 1.0], ['run_forward2', 10], ['delay', 1000], ['rot_body', 0.5], ['delay', 1000], [
                'dance1_2', 0.5], ['dance1_2', 0.5], ['delay', 1000], ['go_back', 2.5], ['to_spider1', 1]]
            origaker.zip_action(order=motions)
        elif motion_number == 82:
            motions = [['to_stick1', 0.5], ['stick_forward', 1.0], ['delay', 1000], [
                'dance2_2', 0.5], ['dance2_2', 0.5], ['delay', 1000], ['roll_body', 0.5], ['to_stick1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 83:
            motions = [['to_stick1', 0.5], ['stick_forward', 1.0], ['delay', 1000], [
                'dance2_1', 0.5], ['dance2_1', 0.5], ['delay', 1000], ['roll_body', 0.5], ['to_stick1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 84:
            origaker.exe_action(action_name='to_stick1', speed=0.5 * speed, path='sys')
            time.sleep(3)
        elif motion_number == 85:
            motions = [['to_spider2', 1.0], ['delay', 1000], ['trans_body', 0.5],
                       ['trans_body', 0.5], ['delay', 1000],
                       ['spider_shake', 0.5], ['delay', 500], ['spider_pack', 0.3]]
            origaker.zip_action(order=motions)
        elif motion_number == 86:
            motions = [['transform', 0.3], ['to_dog1', 0.5], ['serial_forward', 1.0], ['delay', 100],
                       ['shake_head_kay2', 0.5], ['sit_down', 0.5], ['delay', 500], ['sit_up', 0.5],
                       ['to_dog1', 0.5], ['delay', 2000], ['transform_back', 0.5],
                       ['delay', 800], ['to_spider1', 1.0]]
            origaker.zip_action(order=motions)
        elif motion_number == 87 or motion_number == 134:  # 舞蹈1----极乐净土
            if motion_number == 134:
                motions = [['spots_dir_song', 211], ['delay', 5000], ['spots_dir_song', 201]]
                origaker.zip_action(order=motions)
            else:
                time.sleep(5.8)
            motions = [['trans_body', 0.5], ['trans_body', 0.5],
                       ['rot_body', 0.5], ['rot_body', 0.5],
                       ['to_spider1', 0.5], ['dance1_3', 0.8],
                       ['dance1_3', 0.8], ['dance1_3', 0.8], ['go_forward', 0.8],
                       ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8],
                       ['go_back', 0.8], ['turn_left', 0.8], ['dance1_1', 0.7],
                       ['dance1_1', 0.7], ['turn_right', 0.8], ['deform_body', 0.5],
                       ['dance2_1', 0.7], ['dance2_3', 0.7], ['trans_body', 0.5],
                       ['trans_body', 0.5], ['to_stick1', 0.8], ['stick_forward', 0.8],
                       ['dance2_3', 0.7], ['dance2_3', 0.7],
                       ['transform', 0.5], ['to_dog1', 0.5], ['delay', 1800], ['dog_thanks', 0.5], ['sit_up', 0.5],
                       ['transform_back', 0.5]]
            origaker.zip_action(order=motions)
            if motion_number == 134:
                origaker.spots_dir_song(1, 47)
        elif motion_number == 88 or motion_number == 135:  # 舞蹈2----梦想起航
            if motion_number == 135:
                motions = [['spots_dir_song', 212], ['delay', 5000], ['spots_dir_song', 202]]
                origaker.zip_action(order=motions)
            else:
                time.sleep(5.8)
            motions = [['rot_body', 0.5], ['rot_body', 0.5],
                       ['trans_body', 0.5], ['trans_body', 0.5],
                       ['to_spider1', 0.5], ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8],
                       ['go_forward', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8],
                       ['go_back', 0.8], ['turn_left', 0.8], ['dance1_1', 0.7],
                       ['dance1_1', 0.7], ['turn_right', 0.8], ['deform_body', 0.5], ['dance2_1', 0.7],
                       ['dance2_3', 0.7], ['trans_body', 0.5], ['trans_body', 0.5], ['to_stick1', 0.8],
                       ['stick_forward', 0.8], ['dance2_3', 0.7], ['dance2_3', 0.7], ['transform', 0.5],
                       ['to_dog1', 0.5], ['delay', 1000], ['dog_thanks', 0.5], ['sit_up', 0.5],
                       ['transform_back', 0.5], ['to_spider1', 0.5], ['spots_dir_song', 254], ['delay', 100],
                       ['spots_dir_song', 47]]
            origaker.zip_action(order=motions)
        elif motion_number == 89 or motion_number == 136:  # 舞蹈3----动感舞蹈
            if motion_number == 136:
                motions = [['spots_dir_song', 213], ['delay', 5000], ['spots_dir_song', 203]]
                origaker.zip_action(order=motions)
            else:
                time.sleep(5.8)
            motions = [['rot_body', 0.5], ['rot_body', 0.5],
                       ['trans_body', 0.5], ['trans_body', 0.5], ['trans_body', 0.5],
                       ['to_spider1', 0.5], ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8],
                       ['go_forward', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8], ['dance1_3', 0.8],
                       ['go_back', 0.8], ['turn_left', 0.8], ['dance1_1', 0.7],
                       ['dance1_1', 0.7], ['turn_right', 0.8], ['deform_body', 0.5], ['dance2_1', 0.7],
                       ['dance2_3', 0.7], ['dance2_3', 0.7], ['trans_body', 0.5], ['trans_body', 0.5],
                       ['to_stick1', 0.8],
                       ['transform', 0.5], ['delay', 1800], ['dog_thanks', 0.5], ['sit_up', 0.5],
                       ['transform_back', 0.5], ['spots_dir_song', 254], ['delay', 100], ['spots_dir_song', 47]]
            origaker.zip_action(order=motions)
        elif motion_number == 90:
            motions = [['spots_dir_song', 112], ['go_forward', 0.5], ['to_spider1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 91:
            motions = [['spots_dir_song', 114], ['rot_body', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 92:
            motions = [['spots_dir_song', 116], ['rot_body', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 93:
            motions = [['spots_dir_song', 118], ['rot_body', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 94:
            motions = [['spots_dir_song', 120], ['to_stick1', 0.5], ['roll_body', 0.5], ['to_stick1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 95:
            motions = [['spots_dir_song', 122], ['stick_forward', 1.0],
                       ['roll_body', 0.5], ['roll_body', 0.5], ['to_stick1', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 96:
            motions = [['spots_dir_song', 124], ['crab_forward', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 97:
            motions = [['spots_dir_song', 126], ['spider_shake', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 98:
            motions = [['spots_dir_song', 128], ['trans_body', 0.5], ['trans_body', 0.5], ['delay', 100],
                       ['trans_body', 0.5], ['trans_body', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 99:
            motions = [['spots_dir_song', 130], ['trans_body', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 100:
            motions = [['spots_dir_song', 132], ['transform', 0.5]]
            origaker.zip_action(order=motions)
        elif motion_number == 101:
            origaker.spots_dir_song(1, 134)
        elif motion_number == 102:
            origaker.spots_dir_song(1, 136)
        elif motion_number == 103:
            origaker.spots_dir_song(1, 138)
        elif motion_number == 104:
            origaker.spots_dir_song(1, 140)
        elif motion_number == 105:
            origaker.spots_dir_song(1, 142)  # 相声语音
        elif motion_number == 106:
            origaker.spots_dir_song(1, 144)
        elif motion_number == 107:
            origaker.spots_dir_song(1, 146)
        elif motion_number == 108:
            origaker.spots_dir_song(1, 148)
        elif motion_number == 109:
            origaker.spots_dir_song(1, 150)
        elif motion_number == 110:
            origaker.spots_dir_song(1, 152)
        elif motion_number == 121:
            origaker.spots_dir_song(1, 154)
        elif motion_number == 122:
            origaker.spots_dir_song(1, 156)
        elif motion_number == 123:
            origaker.spots_dir_song(1, 158)
        elif motion_number == 124:
            origaker.spots_dir_song(1, 160)
        elif motion_number == 125:
            origaker.spots_dir_song(1, 162)
        if motion_number != 14 and motion_number != 45 and motion_number != 45:
            hn = 0
        if motion_number != 72:
            xn = 0
        # for ir in "{ok}":
        # wi.writechar(ord(ir))
        app_socket.sendto(bytes("{ok}", 'utf-8'), addr)
        flag = 1


def file_copy(filepath, newpath):
    instruct = 'sudo cp -fp ' + filepath + ' ' + newpath
    os.system(instruct)


def get_netlist():
    instruct = 'sudo wpa_cli -i wlan0 list_network'
    raw_data = os.popen(instruct).read()
    list_network, list_id = process_list_network(raw_data)
    return list_network, list_id


class Robot:
    def __init__(self):
        try:
            ip_scan = os.popen('sudo wpa_cli -i wlan0 status|grep \"ip_address\"').read()
            ssid_scan = os.popen('sudo wpa_cli -i wlan0 status|grep ^\"ssid\"').read()
            bssid_scan = os.popen('sudo wpa_cli -i wlan0 status|grep \"bssid\"').read()
            self.ip = process_ip(ip_scan).replace('\n', '')
            self.ssid = process_ssid(ssid_scan).replace('\n', '')
            self.bssid = process_bssid(bssid_scan).replace('\n', '')
            self.robot_id = ROBOT_ID.replace('\n', '')
            # self.action_sys_list = [item.split('.')[0] for item in get_file_list(ACTION_PATH_SYS)]
            self.action_user_list = [item.split('.')[0] for item in get_file_list(ACTION_PATH_USER)]
            # self.code_sys_list = [item.split('.')[0] for item in get_file_list(CODE_PATH_SYS)]
            self.code_user_list = [item.split('.')[0] for item in get_file_list(CODE_PATH_USER)]
            wifi_password = os.popen('sudo cat ' + WIFI_PATH + "|grep -A 4 \"" + self.ssid + "\"").read()
            self.wifi_password = process_wifi_password(wifi_password)
            self.camera_ip = ""
            self.nets = get_num_of_nets()
        except Exception:
            raise

    def udp_connect(self, port):
        try:
            address = ("", port)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind(address)
            while True:
                data, addr = s.recvfrom(2048)
                if data == bytes(ROBOT_ID, 'utf-8'):
                    response = bytes(ROBOT_ID + ' IP: ' + self.ip, 'utf-8')
                    print('response', response)
                    s.sendto(response, addr)
        except Exception:
            raise

    def app_udp_connect(self):
        # global APP_UDP_S
        try:
            # address = ('', APP_UDP_PORT)
            # addr = (ip, port)
            # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # APP_UDP_S.bind(address)
            last_data = []
            while True:
                # data, addr = s.recvfrom(2048)
                data, add = APP_UDP_S.recvfrom(2048)
                # print(add)
                # print("rev:", data)
                # exe_cmd(cmd_list_temp=analyze_data(data), speed=1.0, app_socket=s, addr=add)
                # if (flag):
                try:
                    t1 = threading.Thread(target=exe_cmd,
                                          args=(analyze_data(receive_data(data=data)), 1, APP_UDP_S, add))
                    t1.start()
                except KeyboardInterrupt:
                    print("动作急停!!!")
                    gl.set_value('state', 'WAITING')
                except Exception as result:
                    print('检测出异常{}'.format(result))
                    gl.set_value('state', 'WAITING')
        except Exception:
            gl.set_value('state', 'WAITING')
            raise

    def robot_get_states(self):
        origaker.get_electricity()
        origaker.get_state(level=1)
        try:
            states = {
                'robot_id': self.robot_id,
                'posture': origaker.posture,
                'state': origaker.state,
                'power': origaker.power,
                'ip': self.ip,
                'ssid': self.ssid,
                'bssid': self.bssid
            }
            return states
        except Exception:
            raise

    @staticmethod
    def robot_get_network_list():
        try:
            networks = os.popen("sudo iw dev wlan0 scan |grep \"SSID:\"").read()
            network_list = process_ssid_list(networks)
            return network_list
        except Exception:
            raise

    @staticmethod
    def robot_network_backup():
        from DRcode.app.config.setting import WIFI_PATH
        wifi_path_bak = WIFI_PATH + '.bak'
        file_copy(WIFI_PATH, wifi_path_bak)

    @staticmethod
    def robot_network_restore():
        from DRcode.app.config.setting import WIFI_PATH
        wifi_path_bak = WIFI_PATH + '.bak'
        file_copy(wifi_path_bak, WIFI_PATH)

    @staticmethod
    def robot_delete_backup():
        from DRcode.app.config.setting import WIFI_PATH
        instruct = 'sudo rm -rf ' + WIFI_PATH + '.bak'
        os.system(instruct)

    def robot_if_backup(self, new_ssid):
        new_ssid = str(new_ssid.encode(encoding='utf-8'))[2:-1]
        from DRcode.app.config.secure import WIFI_SSID
        list_network, list_id = get_netlist()
        print('list network', list_network)
        print('list id', list_id)
        if new_ssid == WIFI_SSID:
            return False, None
        elif new_ssid == self.ssid:
            return False, None
        elif new_ssid in list_network:
            index = list_network.index(new_ssid)
            return True, list_id[index]
        else:
            return True, None

    @staticmethod
    def robot_add_network(ssid, secret):
        done = False
        org_id = get_net_id()
        net_id = org_id
        try:
            # 添加网络
            add_network = "sudo wpa_cli -i wlan0 add_network"
            net_id = os.popen(add_network).read().replace('\n', '')
            print("新添加的网络ID:" + str(net_id))
            instruct_config_list = [
                "sudo wpa_cli -i wlan0 set_network " + net_id + " ssid \'\"" + ssid + "\"\'",
                "sudo wpa_cli -i wlan0 set_network " + net_id + " psk \'\"" + secret + "\"\'",
                "sudo wpa_cli -i wlan0 save_config",
            ]
            for i, instruct in enumerate(instruct_config_list):
                os.system(instruct)
            # 验证网络能否使用
            # 第一次重启网络服务
            done = check_wifi_config(org_id, net_id)
            if done:
                print("wifi网络：" + ssid + "连接成功！")
            else:
                print("wifi网络：" + ssid + "连接失败！")
            # 切换回原来的网络
            # 第二次重启网络服务
        except Exception as result:
            print('检测出异常{}'.format(result))
        finally:
            print("正在切换回原来的wifi网络，请稍候。。。")
            change_priority(org_id, net_id)
            restart_wifi()
            # 如果添加的网络可用
            # 更改优先级，保证下次开机连接到新添加的网络
            if done:
                change_priority(net_id, org_id)
                return True
            else:
                return False

    @staticmethod
    def robot_delete_network(net_id):
        try:
            delete_network(net_id)
        except Exception:
            raise

    @staticmethod
    def robot_read_action_frame():
        try:
            return origaker.read_frame()
        except Exception:
            raise

    @staticmethod
    def robot_rename_action(action_name, new_name):
        try:
            filepath_old = ACTION_PATH_USER + action_name + '.txt'
            filepath_new = ACTION_PATH_USER + new_name + '.txt'
            instruct = 'mv ' + filepath_old + ' ' + filepath_new
            os.system(instruct)
        except Exception:
            raise

    @staticmethod
    def robot_rename_code(code_name, new_name):
        try:
            filepath_old = CODE_PATH_USER + code_name + '.py'
            filepath_new = CODE_PATH_USER + new_name + '.py'
            instruct = 'mv ' + filepath_old + ' ' + filepath_new
            os.system(instruct)
        except Exception:
            raise

    @staticmethod
    def robot_add_action(action_name, action_body, path='usr'):
        try:
            write_action(action_name, action_body, path=path)
        except Exception:
            raise

    @staticmethod
    def robot_add_code(code_name, code_body):
        try:
            write_code(code_name, code_body)
        except Exception:
            raise

    @staticmethod
    def robot_delete_action(action_name):
        try:
            file_path = ACTION_PATH_USER + action_name + '.txt'
            instruct = 'sudo rm ' + file_path
            os.system(instruct)
        except Exception:
            raise

    @staticmethod
    def robot_delete_code(code_name):
        try:
            file_path = CODE_PATH_USER + code_name + '.py'
            instruct = 'sudo rm ' + file_path
            os.system(instruct)
        except Exception:
            raise

    @staticmethod
    def robot_show_action(action_name, num, speed):
        if num == 0:
            path = ACTION_PATH_SYS + action_name + '.txt'
            if os.path.isfile(path):
                try:
                    # print('文件路径为：' + ACTION_PATH_SYS + action_name)
                    return origaker.exe_action(action_name=action_name, speed=0.1 * speed, path='sys')
                except Exception:
                    raise
            else:
                raise NotFound()
        else:
            path = ACTION_PATH_USER + action_name + '.txt'
            if os.path.isfile(path):
                try:
                    # print('文件路径为：' + ACTION_PATH_USER + action_name)
                    return origaker.exe_action(action_name=action_name, speed=0.1 * speed, path='usr')
                except Exception:
                    raise
            else:
                raise NotFound()

    @staticmethod
    def robot_show_code(code_name, num):
        if num == 0:
            path = CODE_PATH_SYS + code_name + '.py'
            if os.path.isfile(path):
                try:
                    fd = open(path, "r")
                    exec (fd.read())
                    # print('文件路径为：' + CODE_PATH_SYS + code_name)
                except Exception:
                    raise
                finally:
                    fd.close()
            else:
                raise NotFound()
        else:
            path = CODE_PATH_USER + code_name + '.py'
            if os.path.isfile(path):
                try:
                    fd = open(path, "r")
                    exec (fd.read())
                    # print('文件路径为：' + CODE_PATH_USER + code_name)
                except Exception:
                    raise
                finally:
                    fd.close()
            else:
                raise NotFound()

    @staticmethod
    def robot_voice(order):
        print("语音指令：" + order)
        if order.find('M') > -1:
            file_name = origaker.posture + '_' + order + ".wav"
            mp.play(file=file_name, path="recognition", block=0)
        elif order.find('N') > -1:
            n = int(order[1]) * 100 + int(order[2]) * 10 + int(order[3])
            if n <= 5:
                action_list = ["shake_hand", "go_forward", "go_backward", "turn_left", "turn_right"]
                action_name = origaker.posture + '_' + action_list[n - 1]
                origaker.exe_action(action_name=action_name, speed=1.0, path="sys")
            elif n >= 11 and n <= 17:
                action_list = ["cute", "happy", "angry", "sad", "hungry", "ponder", "tango"]
                action_name = origaker.posture + '_' + action_list[n - 11]
                origaker.exe_action(action_name=action_name, speed=1.0, path="sys")
            elif n == 6:
                if origaker.posture == "gecko":
                    origaker.exe_action(action_name="gecko_roll_body", speed=1.0, path="sys")
                elif origaker.posture == "stick":
                    origaker.exe_action(action_name="stick_arch_body", speed=1.0, path="sys")
                elif origaker.posture == "spider":
                    origaker.exe_action(action_name="tick_arch_body", speed=1.0, path="sys")
            elif n == 7:
                origaker.exe_action(action_name="to_spider2", speed=1.0, path="sys")
            elif n == 8:
                origaker.exe_action(action_name="to_stick", speed=1.0, path="sys")
            elif n == 9:
                origaker.exe_action(action_name="to_gecko", speed=1.0, path="sys")
            elif n == 10:
                origaker.exe_action(action_name="to_dog", speed=1.0, path="sys")
            elif n >= 200:
                if n == 201:
                    origaker.exe_action(action_name="dog_stand_up", speed=0.5, path="sys")
                elif n == 202:
                    origaker.exe_action(action_name="dog_stand_down", speed=0.5, path="sys")
                elif n == 203:
                    origaker.exe_action(action_name="dog_back_tail", speed=0.5, path="sys")
                elif n == 204:
                    origaker.exe_action(action_name="dog_nod_head", speed=1, path="sys")
                elif n == 205:
                    origaker.exe_action(action_name="dog_shake_hand1", speed=1, path="sys")
                elif n == 206:
                    origaker.exe_action(action_name="dog_playful", speed=1, path="sys")
            elif n >= 400:
                if n == 400:
                    origaker.exe_action(action_name="gecko_volatility", speed=1.0, path="sys")
                elif n == 401:
                    origaker.exe_action(action_name="gecko_pack", speed=0.5, path="sys")
                elif n == 402:
                    origaker.exe_action(action_name="gecko_wonder", speed=1, path="sys")
                elif n == 403:
                    origaker.exe_action(action_name="gecko_creep", speed=1, path="sys")
                elif n == 404:
                    origaker.exe_action(action_name="gecko_sleep", speed=1, path="sys")
            elif n >= 600:
                if n == 600:
                    origaker.exe_action(action_name="stick_go_upstairs", speed=1.0, path="sys")
                elif n == 601:
                    origaker.exe_action(action_name="stick_go_downstairs", speed=1.0, path="sys")
                elif n == 602:
                    origaker.exe_action(action_name="stick_pretty", speed=1.0, path="sys")
                if n == 603:
                    origaker.exe_action(action_name="stick_dance_group", speed=1.0, path="sys")
                elif n == 604:
                    origaker.exe_action(action_name="stick_yoga", speed=1.0, path="sys")
                elif n == 605:
                    origaker.exe_action(action_name="stick_run", speed=1.0, path="sys")
                if n == 606:
                    origaker.exe_action(action_name="stick_exercise", speed=1.0, path="sys")
                elif n == 607:
                    origaker.exe_action(action_name="stick_stepping", speed=1.0, path="sys")
                elif n == 608:
                    origaker.exe_action(action_name="stick_tap_dance", speed=1.0, path="sys")
            elif n >= 800:
                if n == 800:
                    origaker.exe_action(action_name="spider_wonder", speed=1.0, path="sys")
                elif n == 801:
                    origaker.exe_action(action_name="spider_laugh", speed=0.5, path="sys")
                elif n == 802:
                    origaker.exe_action(action_name="spider_snicker", speed=1, path="sys")
                elif n == 803:
                    origaker.exe_action(action_name="spider_surprise", speed=1, path="sys")
                elif n == 804:
                    origaker.exe_action(action_name="spider_sleep", speed=1, path="sys")

    @staticmethod
    def robot_mode(mode, num):
        try:
            origaker.set_joint_mode(joint_num=num, mode=mode)
            return num
        except Exception:
            raise

    @staticmethod
    def robot_angle(angle, num):
        try:
            a_s = angle.split(",")
            joint_angle = float(a_s[0])
            speed = int(a_s[1])
            origaker.set_joint_angle(joint_num=num, joint_angle=joint_angle, speed=speed)
            return num
        except Exception:
            raise

    @staticmethod
    def robot_demarcate(num):
        try:
            return origaker.set_p2_list(id_num=num)
        except Exception:
            raise

    @staticmethod
    def stop_music():
        os.system("sudo pkill -f aplay")


get_net_ssid()
