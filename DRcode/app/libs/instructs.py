class Instruct:
    instruct_type = []
    para = []

    @staticmethod
    def execute_stop():
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        robot.stop_music()
        frames = robot.robot_mode('free', 121)
        return frames

    @staticmethod
    def execute_stop_music():
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        robot.stop_music()

    @staticmethod
    def execute_read_action_frame():
        from DRcode.app.libs.robot import Robot
        robot = Robot()
        return robot.robot_read_action_frame()

    @staticmethod
    def execute_action_show(action_name, num, speed):
        from DRcode.app.libs.robot import Robot
        return Robot.robot_show_action(action_name, num=num, speed=speed)

    @staticmethod
    def execute_code_show(code_name, num):
        from DRcode.app.libs.robot import Robot
        return Robot.robot_show_code(code_name, num=num)

    @staticmethod
    def execute_voice(voice_num):
        from DRcode.app.libs.robot import Robot
        return Robot.robot_voice(voice_num)

    # By YJY
    @staticmethod
    def execute_show_code_frame(code_body):
        from DRcode.app.libs.robot import Robot
        # return Robot.robot_show_code(code_name, num=num)
        # for l in code_body:
        #     print(l)
        exec (code_body)

    @staticmethod
    def execute_mode(mode, num):
        from DRcode.app.libs.robot import Robot
        Robot.robot_mode(mode, num)

    @staticmethod
    def execute_angle(angle, num):
        from DRcode.app.libs.robot import Robot
        Robot.robot_angle(angle, num)

    @staticmethod
    def execute_demarcate(num):
        from DRcode.app.libs.robot import Robot
        return Robot.robot_demarcate(num=num)
