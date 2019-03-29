import os

from DRcode.app.libs.error_code import InstructFailed

BASE_PATH = '/home/pi/DRrobot'
VERSION_PATH = BASE_PATH + '/DRdata/versions.txt'
SRC_PATH = BASE_PATH + '/src'
CODE_PATH = BASE_PATH + '/DRcode'
STARTER_PATH = CODE_PATH + '/DRrobot.py'


def read_version():
    # 监测版本标记，选择相应版本
    f = open(VERSION_PATH, 'r')
    line = f.readline()
    versions_ = line.split(' ')
    versions = [version.strip().strip('\n').strip('\r') for version in versions_]
    return versions


def write_file(file_path, content):
    try:
        f = os.open(file_path, os.O_RDWR | os.O_TRUNC)
        os.write(f, bytes(content, 'utf-8'))
        os.close(f)
        return True
    except:
        return False


def starter():
    try:
        instruct = 'nohup sudo python3 -u ' + STARTER_PATH + ">/home/pi/DRrobot/output.py &"
        print('instruct', instruct)
        os.system(instruct)
        return True
    # 启动失败
    except Exception as result:
        print('检测出异常{}'.format(result))
        return InstructFailed(msg='Error{}'.format(result))


# 解压
def uncompressing(save_path, uncompressing_dir):
    instruct = 'unzip ' + save_path + ' -d ' + uncompressing_dir
    os.system(instruct)


if __name__ == '__main__':
    # 启动程序
    # 读取版本信息
    versions = read_version()
    prev_version_ = versions[0]
    version_ = versions[1]
    new_version_ = versions[2]
    print('previous version:', prev_version_)
    print('current version:', version_)
    print('new version', new_version_)

    if new_version_ != 'None':
        # 解压压缩包
        zip_path = SRC_PATH + '/' + new_version_ + '.zip'
        uncompressing(zip_path, BASE_PATH)
        # 重命名
        instruct1 = 'mv ' + CODE_PATH + ' ' + BASE_PATH + '/' + version_
        instruct2 = 'mv ' + BASE_PATH + '/' + new_version_ + ' ' + CODE_PATH
        [os.system(instruct) for instruct in [instruct1, instruct2]]
        try:
            print('starter---------------')
            starter()
        except Exception as result:
            print('检测出异常{}'.format(result))
            # 未成功启动新版本,替换为原版本
            instruct = 'sudo rm -rf /home/pi/DRrobot/DRcode'
            os.system(instruct)
            zip_path = SRC_PATH + '/' + version_ + '.zip'
            uncompressing(zip_path, CODE_PATH)
            # 修改versions.txt
            prev_version = prev_version_
            version = version_
            new_version = 'None'
        else:
            prev_version = version_
            version = new_version_
            new_version = 'None'
        finally:
            # 修改versions.txt
            print('-------------------modify versions.txt-----------------')
            str_version = prev_version + ' ' + version + ' ' + new_version
            write_file(VERSION_PATH, str_version)
    else:
        starter()
