# 令牌有效时间
TOKEN_EXPIRATION = 30 * 24 * 3600

# 树莓派无线网络配置文件的路径
WIFI_PATH = '/etc/wpa_supplicant/wpa_supplicant.conf'

# 用户创建的动作（txt文件）保存的路径
ACTION_PATH_USER = '/home/pi/DRrobot/DRdata/actions/user/'

ACTION_PATH_SYS = '/home/pi/DRrobot/DRdata/actions/system/'

# 用户创建的动作组（python文件）保存的路径
CODE_PATH_USER = '/home/pi/DRrobot/DRdata/codes/user/'

CODE_PATH_SYS = '/home/pi/DRrobot/DRdata/codes/system/'

VOICE_PATH_SYS = '/home/pi/DRrobot/DRdata/voices/system/'
VOICE_PATH_USER = '/home/pi/DRrobot/DRdata/voices/user/'

LIBS_PATH = '/home/pi/DRrobot/DRcode/app/libs/'

BASEURL = ''

BASE_PATH = '/home/pi/DRrobot'
VERSION_PATH = BASE_PATH + '/DRdata/versions.txt'
SRC_PATH = BASE_PATH + '/src'
CODE_PATH = BASE_PATH + '/DRcode'
STARTER_PATH = CODE_PATH + '/DRrobot.py'
