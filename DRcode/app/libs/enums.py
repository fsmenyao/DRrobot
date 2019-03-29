from enum import Enum


class InstructTypeEnum(Enum):
    PAUSE = 1001
    CONTINUE = 1002
    STOP = 1003
    RESET = 1004
    ACTION_FRAME = 2001
    ACTION_FRAME_SHOW = 2002
    ACTION_SHOW_SYS = 3001
    ACTION_SHOW_USER = 3002
    CODE_SHOW_SYS = 4001
    CODE_SHOW_USER = 4002
    #By YJY
    SHOW_CODE_FRAME = 4003
    MODE = 5001
    ANGLE = 5002
    DEMARCATE = 6000
    VOICE = 7000

