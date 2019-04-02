#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from DRcode.app.libs import servo_rpi as se
from DRcode.app.libs import led_cur as lc
from DRcode.app.libs import switch as sw
from DRcode.app.libs import music as mp
import math as cm
from DRcode.app.libs import store_sd as ssd
from DRcode.app.libs.error_code import NotFound
from DRcode.app.config.setting import VOICE_PATH_SYS, LIBS_PATH
import DRcode.app.libs.global_var as gl
import time
from ctypes import cdll
import os
from ctypes import *
import threading
import socket
from DRcode.app.config.secure import DIS_AUDIO_UDP_PORT, APP_UDP_PORT

APP_UDP_S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
APP_UDP_S.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
address = ('', APP_UDP_PORT)
APP_UDP_S.bind(address)

S_addr = ('<broadcast>', DIS_AUDIO_UDP_PORT)


# python中结构体定义
class StructPointer(Structure):
    _fields_ = [("num1", c_float), ("num2", c_float), ("num3", c_float)]


leg = cdll.LoadLibrary(LIBS_PATH + "leg.so")
robot = cdll.LoadLibrary(LIBS_PATH + "leg_robot.so")
leg.inv_c.restype = POINTER(StructPointer)
leg.for_c.restype = POINTER(StructPointer)
robot.go_forward.restype = c_int


def for_kin(theta=[30, 50, 45]):
    angle = c_float * 3
    data = angle()
    data[0] = theta[0]
    data[1] = theta[1]
    data[2] = theta[2]
    p = leg.for_c(data)
    pos = [p.contents.num1, p.contents.num2, p.contents.num3]
    return pos


def inv_kin(pl=[120, 20, 10], ud=0):
    position = c_float * 3
    data = position()
    u_data = c_int(ud)
    data[0] = pl[0]
    data[1] = pl[1]
    data[2] = pl[2]
    p = leg.inv_c(data, u_data)
    pos = [p.contents.num1, p.contents.num2, p.contents.num3]
    if pos[0] == 1000:
        if pos[1] == 1:
            print("给定足尖点超出腿工作空间。。。")
            return False
        elif pos[1] == 0:
            print("足尖点求解过程中出现：ZeroDivisionError")
            return False
    return pos


class MetaRobot(object):
    l_speed_list = []
    pose_list = []
    ID_list = []
    P1_list = []
    P2_list = []
    init_model_angle = []
    init_servo_angle = []
    c_state = 0
    c_angle_list = []  # 当前机器人模型角度
    action_name = ''
    tr = 0
    state = ''
    power = 0
    posture = 'dog'
    box = 0
    error_count = 0

    def __init__(self, ID_list_temp=[], P1_list_temp=[], init_model_angle_temp=[], servo_number=17):
        self.init_servo_angle = [135, 135, 90, 135, 135, 90, 135, 135, 90, 135, 135, 90, 70, 200, 180, 210, 210]
        if len(ID_list_temp) == 0:  # 如果使用缺省值，则默认舵机编号从1开始，依次增加1
            for i in range(servo_number):
                self.ID_list.append(i + 1)
        else:
            self.ID_list = ID_list_temp[:]
        if len(P1_list_temp) == 0:  # 如果使用缺省值，则默认P1=1
            for i in range(servo_number):
                self.P1_list.append(1)
        else:
            self.P1_list = P1_list_temp[:]
        self.init_model_angle = init_model_angle_temp[:]
        self.init_p2_list()
        if self.get_state(level=2):
            if not mp.speak("机器人启动成功"):
                mp.play(file="start_up.wav")

    def exe_action(self, action_name='', speed=1.0, path='usr'):
        action_list = ssd.get_action(action_name=action_name, path=path)
        if action_list:
            self.action_name = action_name
            self.l_speed_list = action_list[0]
            self.pose_list = action_list[1]
        else:
            print(action_name + "执行过程出错 - 文件读取失败！")
            raise NotFound()
        self.do_motion(speed=speed)

    def do_motion(self, speed=1.0, o_r=0, n=0):
        self.init_state()
        try:
            if n == 0:
                if len(self.pose_list) > len(self.l_speed_list):  # 用来兼容原有程序
                    for i in range(len(self.pose_list) - len(self.l_speed_list)):
                        self.l_speed_list.append(10)
                if o_r == 0:
                    for i in range(len(self.pose_list)):
                        DETA_angle_list = list(
                            map(lambda x: cm.fabs(x[0] - x[1]),
                                zip(self.pose_list[i], self.c_angle_list)))
                        ID_list_temp = []
                        pose_list_temp = []
                        if i == 0:  # 每次保留第一个动作，待验证作用
                            ID_list_temp = self.ID_list
                            pose_list_temp = self.pose_list[i]
                        else:
                            for num in range(len(DETA_angle_list)):
                                if DETA_angle_list[num] > 0:
                                    ID_list_temp.append(self.ID_list[num])
                                    pose_list_temp.append(self.pose_list[i][num])
                        if len(ID_list_temp) > 0:
                            step = int(max(DETA_angle_list) / 3)
                            step = int((step * 10 / self.l_speed_list[i]) / speed)
                            if step == 0:
                                step = 1
                            if se.set_angles(ID_list_temp, self.model_to_servo(ID_list_temp, pose_list_temp), step, 1):
                                self.c_angle_list = self.pose_list[i][:]
                else:
                    re_l_speed_list = []
                    m = len(self.l_speed_list)
                    re_l_speed_list.append(self.l_speed_list[0])
                    for i in range(m - 1):
                        re_l_speed_list.append(self.l_speed_list[m - 1 - i])
                    for j in range(len(self.pose_list)):
                        i = len(self.pose_list) - 1 - j
                        DETA_angle_list = list(
                            map(lambda x: cm.fabs(x[0] - x[1]),
                                zip(self.pose_list[i], self.c_angle_list)))
                        ID_list_temp = []
                        pose_list_temp = []
                        if i == len(self.pose_list) - 1:
                            ID_list_temp = self.ID_list
                            pose_list_temp = self.pose_list[i]
                        else:
                            for num in range(len(DETA_angle_list)):
                                if DETA_angle_list[num] > 0:
                                    ID_list_temp.append(self.ID_list[num])
                                    pose_list_temp.append(self.pose_list[i][num])
                        if len(ID_list_temp) > 0:
                            step = int(max(DETA_angle_list) / 3)
                            step = int((step * 10 / re_l_speed_list[j]) / speed)
                            if step == 0:
                                step = 1
                            if se.set_angles(ID_list_temp, self.model_to_servo(ID_list_temp, pose_list_temp), step, 1):
                                self.c_angle_list = self.pose_list[i][:]
                self.get_state(level=0)
            else:
                if se.set_angles(self.ID_list, self.model_to_servo(self.ID_list, self.pose_list[n - 1]), 100, 1):
                    self.c_angle_list = self.pose_list[n - 1][:]
        except:
            self.get_state(level=2)
            raise KeyboardInterrupt

    def model_to_servo(self, ID_list_temp=[], model_angle_list=[]):
        servo_angle_list = model_angle_list[:]
        for i in range(len(model_angle_list)):
            servo_angle_list[i] = self.P1_list[ID_list_temp[i] - 1] * servo_angle_list[i] + self.P2_list[
                ID_list_temp[i] - 1]
        return servo_angle_list

    def servo_to_model(self, ID_list_temp=[], servo_angle_list=[]):
        model_angle_list = servo_angle_list[:]
        # print(ID_list_temp)
        # print(servo_angle_list)
        for i in range(len(ID_list_temp)):
            model_angle_list[i] = int(
                (servo_angle_list[i] - self.P2_list[ID_list_temp[i] - 1]) / self.P1_list[ID_list_temp[i] - 1])
        return model_angle_list

    def clear_pose(self, n=0):
        if n == 0:
            self.l_speed_list = []
            self.pose_list = []
        elif n > 0:
            if n <= len(self.pose_list):
                del self.pose_list[n - 1]

    def set_joint_mode(self, joint_num=121, mode=""):
        # print(mode)
        mode_list = ["damp", "lock", "free"]
        if mode in mode_list:
            if joint_num == 121:
                se.set_mode(id_num=121, mode=mode_list.index(mode) + 1)
            else:
                se.set_mode(id_num=self.ID_list[joint_num - 1], mode=mode_list.index(mode) + 1)
        else:
            print("mode error in set_joint_mode!")

    def set_joint_angle(self, joint_num=1, joint_angle=0, speed=1):
        servo_angle = self.P1_list[joint_num - 1] * joint_angle + self.P2_list[joint_num - 1]
        delta_angle = cm.fabs(self.c_angle_list[joint_num - 1] - joint_angle)
        step = int(delta_angle * 10 / (3 * speed))
        if joint_num in self.ID_list:
            se.set_angle(id_num=self.ID_list[joint_num - 1], angle=servo_angle, step=step)

    @staticmethod
    def check_state(angles=[0, 0, 0]):  # angles为机器人15-17腰部关节模型角度
        angle_15 = angles[0]
        angle_16 = angles[1]
        angle_17 = angles[2]
        c_angle = (angle_16 + angle_17) / 2
        if cm.fabs(c_angle - 180) < 90:
            if angle_15 > 150:
                state = 1  # 壁虎
            elif angle_15 < 60:
                state = 3  # 竹节虫
            else:
                state = 2  # 蜘蛛
        else:
            state = 4  # 小狗
        return state

    def read_joints(self, m_s=0):
        bad_servo = []
        servo_list = []
        for i in range(len(self.ID_list)):
            servo = se.get_state(id_num=self.ID_list[i], para_num=2, o_m=0)
            if servo:
                servo_list.append(servo)
            else:
                bad_servo.append(str(self.ID_list[i]) + '号')
                print("ID号为：" + str(self.ID_list[i]) + "的舵机读取角度失败！")
                if len(self.c_angle_list) > 0:
                    servo_list.append(
                        self.model_to_servo(ID_list_temp=[i + 1], model_angle_list=[self.c_angle_list[i]])[0])
                else:
                    servo_list.append(self.init_servo_angle[i])
        self.c_angle_list = self.servo_to_model(ID_list_temp=self.ID_list, servo_angle_list=servo_list)
        if len(bad_servo) == 0:
            self.state = True
        elif len(bad_servo) == len(self.ID_list):
            self.error_count = self.error_count + 1
            if mp.speak("1至" + str(len(self.ID_list)) + "号舵机读取角度失败！"):
                time.sleep(3)
            else:
                mp.play("read_servo_failed.wav")
            self.state = False
            return False
        else:
            if mp.speak(bad_servo[0]):
                for i in range(len(bad_servo)):
                    if i > 0:
                        mp.speak(bad_servo[i])
                    time.sleep(1)
                mp.speak("舵机读取角度失败！")
                time.sleep(2)
            else:
                mp.play("read_servo_failed.wav")
            self.state = False
            return False
        self.error_count = 0
        if m_s == 0:
            return self.c_angle_list
        else:
            return servo_list

    def read_frame(self):
        servo_list = []
        mode_list = []
        modes = ["damp", "lock", "free"]
        for i in range(len(self.ID_list)):
            data = se.get_state(id_num=self.ID_list[i], para_num=6, o_m=0)
            if data != False:
                [id, angle, mode] = data
                if mode <= 3:
                    servo_list.append(angle)
                    mode_list.append(modes[mode - 1])
                else:
                    print("读取的mode有误：mode=" + str(mode))
                    return False
            else:
                self.error_count = self.error_count + 1
                print("ID号为：" + str(self.ID_list[i]) + "的舵机读取角度失败！")
                if self.error_count > 2:
                    mp.speak(str(i + 1) + "号舵机读取角度失败！")
                self.state = False
                return False
        self.error_count = 0
        self.state = True
        self.c_angle_list = self.servo_to_model(ID_list_temp=self.ID_list, servo_angle_list=servo_list)
        return {'angle_list': self.c_angle_list, 'mode_list': mode_list}

    def get_state(self, level=1):
        # level = 0
        try:
            if self.error_count > 3:
                print("error_count=" + str(self.error_count))
                music_list = ["B002", "B202", "B302", "B501"]
                file_name = self.posture + '_' + music_list[self.c_state - 1] + ".wav"
                mp.play(file=file_name, path="character", block=0)
                self.read_joints()
        except:
            print("error_count>3, some errors emerged!")
        if level == 0:  # 直接通过当前角度确定状态
            self.c_state = self.check_state(angles=self.c_angle_list[-3:])
            posture = ['gecko', 'spider', 'stick', 'dog']
            self.posture = posture[self.c_state - 1]
            return self.c_state
        elif level == 1:  # 读取最后三个舵机角度来判断姿态
            angle_15 = se.get_state(id_num=self.ID_list[-3], para_num=2)
            angle_16 = se.get_state(id_num=self.ID_list[-2], para_num=2)
            angle_17 = se.get_state(id_num=self.ID_list[-1], para_num=2)
            if angle_15 and angle_16 and angle_17:
                self.c_state = self.check_state(angles=self.servo_to_model(ID_list_temp=self.ID_list[-3:],
                                                                           servo_angle_list=[angle_15, angle_16,
                                                                                             angle_17]))
                posture = ['gecko', 'spider', 'stick', 'dog']
                self.posture = posture[self.c_state - 1]
                return self.c_state
            else:
                print("读取腰部关节角度出错！")
                return False
        else:  # 读取所有舵机角度并更新self.c_angle_list,同时判断状态，一般用在初始化上
            if self.read_joints():
                self.c_state = self.check_state(angles=self.c_angle_list[-3:])
                posture = ['gecko', 'spider', 'stick', 'dog']
                self.posture = posture[self.c_state - 1]
                return self.c_state
            else:
                self.c_state = 0
                return False

    def init_state(self):
        if gl.get_value('state') == 'STOP':
            gl.set_value('state', 'WAITING')
            se.set_mode(121, 3)
            self.get_state(level=2)
            # print("正在执行急停指令-stop！！！- INIT_STATE")
            raise KeyboardInterrupt
        if self.tr == 0 and len(self.pose_list) > 0:
            self.get_state(level=0)
            pose = ['壁虎', '蜘蛛', '竹节虫', '小狗']
            # print("当前姿态为：" + pose[self.c_state - 1])
            r_state = self.check_state(angles=self.pose_list[0][-3:])
            if self.c_state != r_state:
                pose = ['壁虎', '蜘蛛', '竹节虫', '小狗']
                # print("准备姿态为：" + pose[r_state - 1])
                c_pose_list = self.pose_list[:]
                if self.c_state == 4:
                    self.tr = 1
                    self.exe_action(action_name='transform_back', speed=0.4)
                    self.tr = 0
                if r_state == 4:
                    self.tr = 1
                    self.exe_action(action_name='transform', speed=0.4)
                    self.tr = 0
                else:
                    pass
                    # print("待完善")
                self.pose_list = c_pose_list[:]

    def set_p2_list(self, id_num=121):
        if id_num == 121:
            servo_angle = self.read_joints(m_s=1)
            if servo_angle:
                delta_value = []
                for i in range(len(servo_angle)):
                    delta_value.append(cm.fabs(self.init_servo_angle[i] - servo_angle[i]))
                if max(delta_value) < 15:
                    p2_list = []
                    for i in range(len(self.P1_list)):
                        p2_list.append(round(servo_angle[i] - self.P1_list[i] * self.init_model_angle[i], 1))
                    self.P2_list = p2_list[:]
                else:
                    print("关节偏差太大，标定失败:" + str(delta_value))
                    return False
            else:
                print("机器人关节标定失败！")
                return False
        else:
            if 0 < id_num <= len(self.ID_list):
                servo_angle = se.get_state(id_num=self.ID_list[id_num - 1], para_num=2)
                if servo_angle:
                    if cm.fabs(servo_angle - self.init_servo_angle[id_num - 1]) < 15:
                        self.P2_list[id_num - 1] = round(
                            servo_angle - self.P1_list[id_num - 1] * self.init_model_angle[id_num - 1], 1)
                    else:
                        print(str(id_num) + "号关节偏差太大，标定失败")
                        return False
                else:
                    print(str(id_num) + "号关节标定失败")
                    return False
        ssd.set_p2_list(self.P2_list)
        # print(self.P2_list)
        return True

    def init_p2_list(self):
        p2_list_temp = ssd.get_p2_list(servo_number=len(self.ID_list))
        if p2_list_temp:
            print("获取存储p2_list成功：")
            self.P2_list = p2_list_temp[:]
            print(self.P2_list)
            return True
        else:
            print("获取存储p2_list失败，采用系统p2_list默认值:")
            self.P2_list = [135, 156.8, 111.8, 135, 156.8, 111.8, 135, 156.8, 111.8, 135, 156.8, 111.8, -20,
                            290, 0, 30, 30]
            print(self.P2_list)
            return False

    # 机器人扩展动作组
    def goto_shape(self, attitude='gecko', speed=0.5):
        if attitude == 'gecko':
            return self.exe_action(action_name='to_gecko', speed=speed, path='sys')
        elif attitude == 'spider':
            return self.exe_action(action_name='to_spider', speed=speed, path='sys')
        elif attitude == 'stick':
            return self.exe_action(action_name='to_stick', speed=speed, path='sys')
        elif attitude == 'dog':
            return self.exe_action(action_name='to_dog', speed=speed, path='sys')
        else:
            print("未知形态 - goto_shape")
            return False

    def show_action(self, attitude="gecko", action="shake_hand", speed=0.5):
        if attitude == 'gecko':
            return self.exe_action(action_name='gecko_' + action, speed=speed, path='sys')
        elif attitude == 'spider':
            return self.exe_action(action_name='spider_' + action, speed=speed, path='sys')
        elif attitude == 'stick':
            return self.exe_action(action_name='stick_' + action, speed=speed, path='sys')
        elif attitude == 'dog':
            return self.exe_action(action_name='dog_' + action, speed=speed, path='sys')
        else:
            print("未知形态 - show_action")
            return False

    def zip_action(self, order=[]):
        for i in range(len(order)):
            if order[i][0] == 'delay':
                time.sleep(order[i][1] / 1000)
            elif order[i][0] == 'spots_dir_song':
                self.spots_dir_song(num2=order[i][1])
            else:
                self.exe_action(action_name=order[i][0], speed=order[i][1], path="sys")

    def dance(self, dance_number="seaweed"):
        if dance_number == "seaweed":
            file_name = "海草舞.wav"
            if self.c_state == 4:
                self.exe_action(action_name="transform_back", speed=0.5, path="sys")
            mp.play(file=file_name, path="music", block=0)
            motions = [['dance1', 0.7], ['rot_body', 0.7], ['turn_right', 0.8], ['dance3', 0.7],
                       ['turn_left', 0.8], ['dance1', 0.7], ['rectangle', 0.3], ['dance3', 0.7],
                       ['deform_body', 0.4], ['dance4', 0.7], ['stick_trunk', 0.3],
                       ['triangle', 0.3], ['dance2', 0.7], ['dance4', 0.7], ['trans_body', 0.3],
                       ['spider_shake', 0.5], ['to_spider2', 0.5]]
            self.zip_action(order=motions)
        elif dance_number == "happiness":
            file_name = "可爱颂.wav"
            mp.play(file=file_name, path="music", block=0)
            motions = [['transform', 0.4], ['tabu', 0.3],
                       ['serial_hand', 0.3], ['serial_dance', 0.3], ['serial_dance', 0.3], ['sit_up', 0.3],
                       ['transform_back', 0.3], ['turn_right', 1.0], ['turn_right', 1.0], ['turn_right', 1.0],
                       ['to_spider2', 0.5]]
            self.zip_action(order=motions)
        elif dance_number == "exercise":
            file_name = "广播体操.wav"
            if self.c_state == 4:
                self.exe_action(action_name="transform_back", speed=0.5, path="sys")
            mp.play(file=file_name, path="music", block=0)
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
                       ['delay', 500], ['spider_shake', 0.5]]
            self.zip_action(order=motions)
        elif dance_number == "paradise":
            file_name = "极乐净土.wav"
            if self.c_state == 4:
                self.exe_action(action_name="transform_back", speed=0.5, path="sys")
            mp.play(file=file_name, path="music", block=0)
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
            self.zip_action(order=motions)
        elif dance_number == "youth":
            file_name = "青春修炼手册.wav"
            self.exe_action(action_name="to_spider1", speed=0.5, path="sys")
            mp.play(file=file_name, path="music", block=0)
            motions = [['delay', 6800], ['gecko_yaohuang', 0.3], ['circle_right', 0.4], ['circle_left', 0.4],
                       ['delay', 200], ['to_gecko', 0.7], ['gecko_roll_body', 0.5],
                       ['delay', 500], ['trans_body', 0.3], ['turn_right', 0.8], ['turn_left', 0.8],
                       ['spider_change', 0.4], ['delay', 500], ['rectangle_1', 0.7], ['to_stick', 0.7],
                       ['stick_pa', 0.5],
                       ['to_stick', 0.7], ['stick_trunk', 0.5], ['stick_trunk', 0.5], ['stick_fuwocheng', 0.7],
                       ['stick_dian', 0.5], ['stick_right', 0.8], ['stick_right', 0.8], ['stick_right', 0.8],
                       ['to_stick', 0.7], ['stick_dian', 0.5], ['stick_dian2', 0.4],
                       ['out_box1', 0.5], ['dog_lash_tail', 0.5], ['dog_yaobai', 0.5], ['dog_baidong', 0.5],
                       ['dog_hands', 0.4], ['delay', 200], ['dog_circle_left', 0.3],
                       ['dog_circle_right', 0.3], ['triangle1', 0.7], ['turn_left', 0.8], ['turn_left', 0.8],
                       ['trans_body', 0.3], ['spider_shake_hand', 0.5], ['to_spider1', 0.7]]
            self.zip_action(order=motions)

    # 机器人部件控制
    def set_leg_position(self, leg_number=1, position=[0, 0, 0], speed=1.5):
        if self.get_state(level=1) and self.posture == "dog":
            joints = inv_kin(pl=position, ud=1)
        else:
            joints = inv_kin(pl=position, ud=0)
        if joints != False:
            self.clear_pose()
            pose = self.c_angle_list[:]
            pose[3 * (leg_number - 1)] = joints[0]
            pose[3 * (leg_number - 1) + 1] = joints[1]
            pose[3 * (leg_number - 1) + 2] = joints[2]
            self.pose_list.append(pose)
            return self.do_motion(speed=speed)

    def get_leg_joints(self, leg_number=1):
        ID_list = self.ID_list[3 * (leg_number - 1):3 * (leg_number - 1) + 3]
        servo_angle = []
        for id in ID_list:
            angle = se.get_state(id, 2)
            if angle != False:
                servo_angle.append(angle)
            else:
                print("读取" + str(id) + "号关节角度失败")
                return False
        joints = self.servo_to_model(ID_list_temp=ID_list, servo_angle_list=servo_angle)
        return joints

    def set_leg_joints(self, leg_number=1, joints=[0, 0, 0], speed=1.5):
        self.clear_pose()
        pose = self.c_angle_list[:]
        pose[3 * (leg_number - 1)] = joints[0]
        pose[3 * (leg_number - 1) + 1] = joints[1]
        pose[3 * (leg_number - 1) + 2] = joints[2]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def get_leg_position(self, leg_number=1):
        ID_list = self.ID_list[3 * (leg_number - 1):3 * (leg_number - 1) + 3]
        servo_angle = []
        for id in ID_list:
            angle = se.get_state(id, 2)
            if angle != False:
                servo_angle.append(angle)
            else:
                print("读取" + str(id) + "号关节角度失败")
                return False
        joints = self.servo_to_model(ID_list_temp=ID_list, servo_angle_list=servo_angle)
        return for_kin(theta=joints)

    def set_joint(self, leg_number=1, joint=1, angle=1, step=10):
        self.clear_pose()
        pose = self.c_angle_list[:]
        pose[3 * (leg_number - 1) + joint - 1] = angle
        self.pose_list.append(pose)
        return self.do_motion(speed=step)

    def set_joint1(self, leg_number=1, angle=0, speed=1.5):
        self.clear_pose()
        pose = self.c_angle_list[:]
        if angle < -90:
            angle = -90
        elif angle > 90:
            angle = 90
        pose[3 * (leg_number - 1)] = angle
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_joint2(self, leg_number=1, angle=0, speed=1.5):
        self.clear_pose()
        pose = self.c_angle_list[:]
        if angle < -100:
            angle = -100
        elif angle > 100:
            angle = 100
        pose[3 * (leg_number - 1) + 1] = angle
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_joint3(self, leg_number=1, angle=0, speed=1.5):
        self.clear_pose()
        pose = self.c_angle_list[:]
        if angle <= -135:
            angle = -135
        elif angle >= 135:
            angle = 135
        pose[3 * (leg_number - 1) + 2] = angle
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def get_joint(self, leg_number=1, joint=1):
        ID = self.ID_list[3 * (leg_number - 1) + joint - 1]
        servo_angle = []
        angle = se.get_state(ID, 2)
        if angle != False:
            servo_angle.append(angle)
        else:
            print("读取" + str(ID) + "号关节角度失败")
            return False
        joint_angle = self.servo_to_model(ID_list_temp=[ID], servo_angle_list=servo_angle)
        return joint_angle

    def set_gecko_shape(self, angle=0, speed=1):
        self.get_state(level=1)
        if self.posture == "dog":
            self.exe_action(action_name='transform_back', speed=0.5)
        waist_joint = [90 - angle, 90, 180 - angle, 180, 180]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_gecko_shape_expandable(self, angle_list=[30, 120], speed=1):
        self.get_state(level=1)
        if self.posture == "dog":
            self.exe_action(action_name='transform_back', speed=0.5)
        waist_joint = [180 - angle_list[1] / 2, 180 - angle_list[1] / 2, angle_list[1], 180 - angle_list[0],
                       180 - angle_list[0]]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_gecko_shape_twist(self, angle=30, speed=1):
        self.get_state(level=1)
        if self.posture == "dog":
            self.exe_action(action_name='transform_back', speed=0.5)
        waist_joint = [90 - angle, 90 - angle, 180 - 2 * angle, 180, 180]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_spider_shape(self, angle=120, speed=1):
        self.get_state(level=1)
        if self.posture == "dog":
            self.exe_action(action_name='transform_back', speed=0.5)
        waist_joint = [180 - angle / 2, 180 - angle / 2, angle, 180, 180]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_stick_shape(self, angle=0, speed=1):
        self.get_state(level=1)
        if self.posture == "dog":
            self.exe_action(action_name='transform_back', speed=0.5)
        if angle > 90:
            angle = 90
        waist_joint = [170, 170, 20, 180 - angle, 180 - angle]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def set_dog_shape(self, angle_list=[90, 180, 90], speed=1):
        self.get_state(level=1)
        if self.posture != "dog":
            self.exe_action(action_name='transform', speed=0.5)
        waist_joint = [angle_list[0], angle_list[2], angle_list[1], 0, 0]
        self.clear_pose()
        pose = self.c_angle_list[:]
        for i in range(len(waist_joint)):
            pose[-1 * (i + 1)] = waist_joint[-1 * (i + 1)]
        self.pose_list.append(pose)
        return self.do_motion(speed=speed)

    def go_forward(self, attitude="gecko", length=100, height=50, speed=1):
        para = c_float * 3
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = length
            data[2] = height
            try:
                if robot.go_forward(data) == 1:
                    self.exe_action(action_name="gecko_go_forward0", speed=speed, path='sys')
                else:
                    return False
            except Exception as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = length
            data[2] = height
            try:
                if robot.go_forward(data) == 1:
                    self.exe_action(action_name="spider_go_forward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = length
            data[2] = height
            try:
                if robot.go_forward(data) == 1:
                    self.exe_action(action_name="stick_go_forward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = length
            data[2] = height
            try:
                if robot.go_forward(data) == 1:
                    self.exe_action(action_name="dog_go_forward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    def go_backward(self, attitude="gecko", length=100, height=50, speed=1):
        para = c_float * 3
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = length
            data[2] = height
            try:
                if robot.go_backward(data) == 1:
                    self.exe_action(action_name="gecko_go_backward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = length
            data[2] = height
            try:
                if robot.go_backward(data) == 1:
                    self.exe_action(action_name="spider_go_backward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = length
            data[2] = height
            try:
                if robot.go_backward(data) == 1:
                    self.exe_action(action_name="stick_go_backward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = length
            data[2] = height
            try:
                if robot.go_backward(data) == 1:
                    self.exe_action(action_name="dog_go_backward0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    def turn_left(self, attitude="gecko", angle=45, height=50, speed=1):
        para = c_float * 3
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_left(data) == 1:
                    self.exe_action(action_name="gecko_turn_left0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_left(data) == 1:
                    self.exe_action(action_name="spider_turn_left0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_left(data) == 1:
                    self.exe_action(action_name="stick_turn_left0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_left(data) == 1:
                    self.exe_action(action_name="dog_turn_left0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    def turn_right(self, attitude="gecko", angle=45, height=50, speed=1):
        para = c_float * 3
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_right(data) == 1:
                    self.exe_action(action_name="gecko_turn_right0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_right(data) == 1:
                    self.exe_action(action_name="spider_turn_right0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_right(data) == 1:
                    self.exe_action(action_name="stick_turn_right0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = angle
            data[2] = height
            try:
                if robot.turn_right(data) == 1:
                    self.exe_action(action_name="dog_turn_right0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    def rotate_roll(self, attitude="gecko", angle=15, speed=1):
        para = c_float * 2
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = angle
            try:
                if robot.roll(data) == 1:
                    self.exe_action(action_name="gecko_roll0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = angle
            try:
                if robot.roll(data) == 1:
                    self.exe_action(action_name="spider_roll0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = angle
            try:
                if robot.roll(data) == 1:
                    self.exe_action(action_name="stick_roll0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = angle
            try:
                if robot.roll(data) == 1:
                    self.exe_action(action_name="dog_roll0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    def rotate_pitch(self, attitude="gecko", angle=15, speed=1):
        para = c_float * 2
        data = para()
        if attitude == "gecko":
            data[0] = 1
            data[1] = angle
            try:
                if robot.pitch(data) == 1:
                    self.exe_action(action_name="gecko_pitch0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "spider":
            data[0] = 2
            data[1] = angle
            try:
                if robot.pitch(data) == 1:
                    self.exe_action(action_name="spider_pitch0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "stick":
            data[0] = 3
            data[1] = angle
            try:
                if robot.pitch(data) == 1:
                    self.exe_action(action_name="stick_pitch0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        elif attitude == "dog":
            data[0] = 4
            data[1] = angle
            try:
                if robot.pitch(data) == 1:
                    self.exe_action(action_name="dog_pitch0", speed=speed, path='sys')
                else:
                    return False
            except BaseException as result:
                print('检测出异常{}'.format(result))
                raise KeyboardInterrupt
        return True

    # 全色灯模块
    def set_led_color(self, leg_number=1, led=1, color="#330099"):
        if len(color) == 7 and color[0] == '#':
            h = "0x"
            ex = color[1:3]
            red = int(h + ex, 16)
            ex = color[3:5]
            green = int(h + ex, 16)
            ex = color[5:7]
            blue = int(h + ex, 16)
            lc.set_ledcolor(id=leg_number, sort=led, red=red, green=green, blue=blue)
        else:
            print("color parameters error！")
        time.sleep(0.1)

    def set_leds_mode(self, leg_number=1, mode=5):
        lc.set_leds(id=leg_number, state=mode)
        time.sleep(0.05)

    def set_leds_style(self, leg_list=[1, 2, 3, 4], style="morning"):
        if style == "morning":
            for i in range(len(leg_list)):
                for j in range(6):
                    self.set_led_color(leg_number=leg_list[i], led=j + 1, color="#33ff33")
                self.set_leds_mode(leg_number=leg_list[i], mode=2, time=0)
        elif style == "policeman":
            for i in range(len(leg_list)):
                self.set_led_color(leg_number=leg_list[i], led=1, color="#cc0000")
                self.set_led_color(leg_number=leg_list[i], led=2, color="#cc0000")
                self.set_led_color(leg_number=leg_list[i], led=3, color="#ffff00")
                self.set_led_color(leg_number=leg_list[i], led=4, color="#ffff00")
                self.set_led_color(leg_number=leg_list[i], led=5, color="#000099")
                self.set_led_color(leg_number=leg_list[i], led=6, color="#000099")
                self.set_leds_mode(leg_number=leg_list[i], mode=3, time=0)
        elif style == "warning":
            for i in range(len(leg_list)):
                for j in range(6):
                    self.set_led_color(leg_number=leg_list[i], led=j + 1, color="#cc0000")
                self.set_leds_mode(leg_number=leg_list[i], mode=5, time=0)

    def get_torque_value(self, leg_number=1):
        return lc.get_current(id=leg_number)

    def get_land_state(self, leg_number=1):
        if lc.get_current(id=leg_number) > 1024:
            return True
        else:
            return False

    def set_leds_time(self, leg_number=1, time=10):
        lc.set_time(id=leg_number, duratime=time)
        time.sleep(0.05)

    def set_led_on(self, leg_number=1, led=1):
        lc.set_led(id=leg_number, sort=led, state=1)
        time.sleep(0.05)

    def set_led_off(self, leg_number=1, led=1):
        lc.set_led(id=leg_number, sort=led, state=0)
        time.sleep(0.05)

    def set_led_init(self, leg_number=1):
        lc.flash_init(id=leg_number)
        time.sleep(0.05)

    def set_leds_frequency(self, mode=1, frequency=10):
        if mode == 1:
            cycle = frequency // 200
        elif mode == 2:
            cycle = frequency // 120
        elif mode == 3:
            cycle = frequency // 60
        elif mode == 4:
            cycle = frequency // 20
        for i in range(4):
            lc.write_flash(id=i + 1, addr=4 + mode, value=cycle)
            time.sleep(0.05)

    def get_leds_mode(self, leg_number=1):
        return lc.read_runpara(id=leg_number, ch=2)

    def get_leds_state(self, leg_number=1):
        return lc.read_runpara(id=leg_number, ch=1)

    # 开关模块
    @staticmethod
    def turn_off():
        sw.shut_down()

    def get_attitude(self):
        self.get_state(level=1)
        print("当前机器人姿态为：" + self.posture)
        return self.posture

    def get_electricity(self):
        p = 0
        N = 0
        for i in range(5):
            power = sw.get_voltage()
            n = 5
            while (not power) and n > 0:
                n = n - 1
                power = sw.get_voltage()
            if power:
                p = p + power
                N = N + 1
            else:
                print("读取电量失败")
        if N == 5:
            print("电池剩余电量为", p / 5, "mAh")
            if p > 10000:
                p = 10000
            self.power = int(p / 100)
            if self.power <= 5:  # 电量过低提示（语音+动作）
                music_list = ["B001", "B201", "B301", "B500"]
                file_name = self.posture + '_' + music_list[self.c_state - 1] + ".wav"
                mp.play(file=file_name, path="character", block=0)
                action = "low_battery"
                action_name = self.posture + '_' + action
                self.exe_action(action_name=action_name, speed=1.0, path="sys")
            return self.power
        else:
            print("电量开关板出现故障，请检查！！")

    # mp3
    @staticmethod
    def say(words=""):
        if not mp.speak(text=words):
            mp.play("internet_offline.wav")

    @staticmethod
    def play(music=""):
        if music == "sea":
            mp.play(file="大海.wav", path="music", block=1)
        elif music == "shoes":
            mp.play(file="白色球鞋.wav", path="music", block=1)
        elif music == "camel":
            mp.play(file="沙漠骆驼.wav", path="music", block=1)

    def spots_dir_song(self, num1=1, num2=0x06):
        if 1 <= num2 <= 255:
            global APP_UDP_S, S_addr
            data = [0x7E, 0x05, 0x42, 0x01, 0x06, 0x46, 0xEF]
            data[3] = num1
            data[4] = num2
            data[5] = data[1] ^ data[2] ^ data[3] ^ data[4]
        if self.box == 0:
            if num2 < 10:
                wav = "00" + str(num2) + ".wav"
            elif num2 < 100:
                wav = "0" + str(num2) + ".wav"
            else:
                wav = str(num2) + ".wav"
            mp.play(file=wav, path="app", block=0)
        else:
            APP_UDP_S.sendto(bytes(data), S_addr)

    @staticmethod
    def self_introduction():
        if not mp.speak(text="大家好，我叫Origaker,我有17个自由度。我可以灵活变形，模仿不同的动物"):
            mp.play(file="self_introduction.wav")
