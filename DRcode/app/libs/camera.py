# coding=utf-8
import socket
from DRcode.app.libs.crc8 import Crc8
import DRcode.app.libs.global_var as gl

MYGROUP = '224.1.1.1'
MYPORT = 7001


def creat_content(ssid, password_, ip, bssid):
    password = password_ + '1'
    guide_code = [515, 514, 513, 512]
    password_len = len(password)
    ssid_len = len(ssid)
    total_len = 5 + 4 + password_len + ssid_len
    ssid_crc = get_crc(ssid, 1)
    bssid_list = get_bssid_list(bssid)

    bssid_crc = get_crc(bssid_list, 0)
    datum_data = [total_len, password_len, ssid_crc, bssid_crc]
    ip_address = get_ip_list(ip)
    ap_password = [ord(str) for str in password]
    ap_ssid = [ord(str) for str in ssid]
    data = ip_address + ap_password + ap_ssid
    total_data = datum_data + data
    total_data_xor = 0
    for num in total_data:
        total_data_xor ^= num
    datum_data.append(total_data_xor)
    return guide_code, datum_data, data


def get_crc(list, str):
    crc = Crc8()
    list_num = list
    if str:
        list_str = list
        list_num = [ord(str) for str in list_str]
    [crc.update(num) for num in list_num]
    return crc.value & 0xFF


def get_ip_list(ip):
    return [int(num) for num in ip.split('.')]


def get_bssid_list(bssid):
    return [int(num, 16) for num in bssid.split(':')]


def get_upper_lower(num):
    high_ = num & 0xF0
    high = high_ >> 4
    low = num & 0x0F
    word = [high, low]
    return word[0], word[1]


def get_content(guide_code, datum_data, data):
    messages = []
    content_data = datum_data + data
    length = len(content_data)
    for k in range(20):
        messages.extend(guide_code)
    for j in range(25):
        for k, num in enumerate(content_data):
            crc = get_crc([num, k], 0)
            crc_high, crc_low = get_upper_lower(crc)
            data_high, data_low = get_upper_lower(num)
            message_1 = (crc_high*16 + data_high + 40) & 0x1FF
            message_2 = 296 + k % length
            message_3 = (crc_low*16 + data_low + 40) & 0x1FF
            message = [message_1, message_2, message_3]
            messages.extend(message)
    return messages


def add_contents(num_list):
    all_msg = []
    for num in num_list:
        words = []
        for i in range(num):
            words.append('a')
        one_msg = ''.join(words)
        all_msg.append(one_msg)
    return all_msg


class Camera:

    @staticmethod
    def start_camera():
        from DRcode.app.libs.camera_board import turn_on
        turn_on()

    @staticmethod
    def close_camera():
        from DRcode.app.libs.camera_board import turn_off
        turn_off()

    # 获取摄像头电源开关状态
    @staticmethod
    def get_camera_state():
        from DRcode.app.libs.camera_board import get_camera_state
        return get_camera_state()


class Camera_UDP:

    def __init__(self, port):
        from DRcode.app.libs.robot import Robot
        import struct
        robot = Robot()
        self.ip = robot.ip
        self.bssid = robot.bssid
        self.addr = (robot.ip, port)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(self.addr)

        ttl_bin = struct.pack('@i', 255)
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                          socket.inet_aton(MYGROUP) + socket.inet_aton(self.ip))

    def send_message(self, ssid, passphrase):
        print('UDP send message------------------------------')
        guide_code, datum_data, data = creat_content(ssid, passphrase, self.ip, self.bssid)
        messages = get_content(guide_code, datum_data, data)
        k = 0
        while gl.get_value('camera_connecting'):
            for i, msg in enumerate(add_contents(messages)):
                if i % 5 == 0:
                    k += 1
                MYGROUP = '224' + '.' + str(k % 100) + '.' + str(k % 100) + '.' + str(k % 100)
                self.s.sendto(bytes(msg, 'utf-8'), (MYGROUP, MYPORT))

        self.s.close()
        return True


class Camera_TCP:

    def __init__(self, port):
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        self.ip = robot.ip
        self.addr = (robot.ip, port)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(self.addr)
        self.s.listen(2)

    def receive_message(self):
        connetion, client_address = self.s.accept()
        print("Connection from: ", client_address)
        data = connetion.recv(1024)
        [connetion.send(bytes('OK', 'utf-8')) for i in range(10)]
        gl.set_value('camera_ip', data)
        print('Connected！ IP: ', data)
        gl.set_value('camera_connecting', False)
        connetion.close()
        self.s.close()
        return True

    def get_camera_ip(self):
        print('get camera ip')
        return str(gl.get_value('camera_ip'), 'utf-8')
