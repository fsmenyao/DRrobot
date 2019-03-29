#!/usr/bin/python3
from DRcode.app.config.setting import ACTION_PATH_USER
from DRcode.app.config.setting import ACTION_PATH_SYS
from DRcode.app.config.setting import LIBS_PATH


def set_p2_list(p2_list_temp=[]):
    string = ""
    for i in range(len(p2_list_temp)):
        string += str(p2_list_temp[i])
        string += ' '
    string += '\n'
    file = open(LIBS_PATH + 'p2_list.txt', 'w')
    try:
        file.write(string)
    finally:
        file.close()
    print(get_p2_list())
    return True


def get_p2_list(servo_number=17):
    file = open(LIBS_PATH + 'p2_list.txt', 'rU')
    line_temp = file.readline()
    file.close()
    p2_list_temp = []
    lists = line_temp.split()
    for element in lists:
        p2_list_temp.append(float(element))
    if p2_list_temp != False:
        return p2_list_temp
    else:
        return False


def get_action(action_name='', path="usr"):
    try:
        if path == 'sys':
            path0 = ACTION_PATH_SYS
        else:
            path0 = ACTION_PATH_USER
        path1 = action_name + '.txt'
        path = path0 + path1
        file = open(path, 'rU')
        line_list = file.readlines()
    except IOError:
        print(action_name + '数据读取出错')
        return False
    finally:
        file.close()
    l_speed_list = []
    lists = line_list[0].split()
    for element in lists:
        l_speed_list.append(float(element))
    pose_list = []
    del line_list[0]
    for i in range(len(line_list)):
        pose = []
        lists = line_list[i].split()
        for element in lists:
            pose.append(float(element))
        if len(pose) > 0:
            pose_list.append(pose)
    # print(action_name + ' is loaded successfully!')
    return [l_speed_list, pose_list]
