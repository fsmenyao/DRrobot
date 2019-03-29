from DRboot import write_file, read_version
from DRcode.app.config.setting import BASEURL, SRC_PATH
from DRcode.app.libs.error_code import NotFound, InstructSuccess
from DRcode.app.libs.redprint import Redprint
from DRcode.app.config.secure import VERSION_PATH
import os

api = Redprint('update')


# 下载新版本
def download_version(url, save_path):
    try:
        instruct = 'sudo wget --no-check-certificate ' + url + ' -O ' + save_path
        os.system(instruct)
        return True
    except Exception as result:
        print('检测出异常{}'.format(result))
        return NotFound(msg='Error{}'.format(result))


@api.route('/<filename>', methods=['GET'])
# @auth.login_required
def update_version(filename):
    curr_version = filename.split('.')[0]
    url = BASEURL + '/' + curr_version + '/zip/master'
    zip_path = SRC_PATH + '/' + filename
    # 若成功下载新版本
    if download_version(url, zip_path):
        # 并标记有新的版本
        versions = read_version()
        prev_version = versions[0]
        version = versions[1]
        new_version = curr_version
        print('previous version:', prev_version)
        print('current version:', version)
        print('new version', new_version)
        str_version = prev_version + ' ' + version + ' ' + new_version
        write_file(VERSION_PATH, str_version)
    return InstructSuccess()
