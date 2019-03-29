from aip import AipSpeech
import subprocess
import os
from DRcode.app.config.setting import VOICE_PATH_SYS

""" 你的 APPID AK SK """
APP_ID = '15349517'
API_KEY = 'asalAFmUO8DAyWr4TUXon5xK'
SECRET_KEY = 'FDPRoKzuSh6pBQvr4K6aMbLfkSR2OKTa '

client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)


def speak(text='大然', ch=0):
    try:
        result = client.synthesis(text, 'zh', 1, {
            'vol': 7, 'aue': 6
        })
        print("read: " + text)
        #  识别正确返回语音二进制 错误则返回dict 参照下面错误码
        if not isinstance(result, dict):
            with open('dr_audio.wav', 'wb') as f:
                f.write(result)
            if ch == 0:
                p = subprocess.Popen("sudo aplay dr_audio.wav", shell=True, stderr=subprocess.STDOUT,
                                     stdout=subprocess.PIPE)
                # print(p.pid)   可以用kill杀死进程
            else:
                os.system("sudo aplay dr_audio.wav")
        return True
    except Exception as result:
        print('检测出异常{}'.format(result))
        return False


def play(file='', path="setting", block=1):
    try:
        print(str(block) + "播放：" + '/' + path + '/' + file)
        if path == "setting":  # 系统音效
            order = "sudo aplay " + VOICE_PATH_SYS + "setting/" + file
        elif path == "recognition":  # 语音识别
            order = "sudo aplay " + VOICE_PATH_SYS + "recognition/" + file
        elif path == "app":  # 智能佳app
            order = "sudo aplay " + VOICE_PATH_SYS + "app/" + file
        elif path == "music":  # 播放音乐
            order = "sudo aplay " + VOICE_PATH_SYS + "music/" + file
        elif path == "character":  # 机器人性格特有声音
            order = "sudo aplay " + VOICE_PATH_SYS + "character/" + file
        else:
            print("找不到指定文件路径：" + path)
            return False
        if block == 1:
            os.system(order)
        else:
            p = subprocess.Popen(order, shell=True, stderr=subprocess.STDOUT,
                                 stdout=subprocess.PIPE)
        return True
    except Exception as result:
        print('检测出异常{}'.format(result))
        return False
