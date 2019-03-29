from .app import Flask


def register_blueprints(app):
    from DRcode.app.api import create_blueprint
    app.register_blueprint(create_blueprint(), url_prefix='/v1')


def create_global_var():
    import DRcode.app.libs.global_var as gl
    gl.set_value('state', 'WAITING')
    gl.set_value('stop', 0)
    gl.set_value('start', 0)
    gl.set_value('camera_open', False)
    gl.set_value('camera_connecting', True)
    gl.set_value('camera_ip', '')


def create_app():
    app = Flask(__name__)
    app.config.from_object('DRcode.app.config.setting')
    app.config.from_object('DRcode.app.config.secure')
    register_blueprints(app)
    return app


def check_ps():
    return True
    # os.system('sudo pkill -f python3')
    # key_work = '\"sudo python3 /home/pi/DRrobot/DRrobot.py\"'
    # instruct = 'ps -aux | grep ' + key_work
    # key_line = os.popen(instruct).read()
    # ps_num = key_line[6:14].strip()
    # instruct = 'sudo kill -9' + ps_num
    # os.system(instruct)
    # # key_work = 'sudo python3'
    # instruct = 'sudo killall -9 sudo python3'
    # os.system('sudo killall -9 sudo python3')
    # os.system('nohup sudo python3 -u /home/pi/DRrobot/DRrobot.py >output.txt 2>&1 &')
