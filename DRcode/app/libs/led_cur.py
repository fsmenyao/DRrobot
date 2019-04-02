

import serial
import math as cm
import time

uart = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)
"""
created by MrWang  2018.10.16
电量显示开关板及全色灯电流读取板 库

初始化波特率为19200  在writedata函数中将波特率修改为了115200
在每个函数结束后 将波特率重新初始化为19200
get_voltige 与 fullcolor_get_current

电量显示开关板函数
sw_ctl(state=0)     //无需ID  一个机器人上只有一个电量显示板
led_ctl(state=1)    //state 取值范围1-3  表示三种闪烁样式
get_voltage()       //返回当前电池电压及电量值


全色灯电流传感器板       0x78（120） 为全色灯模块广播号
fullcolor_get_current(id=0)       //返回通过对应ID板子的电流值  id=0x78 时 可读取板子ID
fullcolorled(id=0,led_num=1,red=100,green=100,blue=100)    //控制对应ID板子  led编号下的LED灯状态  三个参数为RGB值
fullcolorled_ctl(id=0,brightness=20,led1=146,led2=146,led3=146,led4=146)    //单条指令控制对应ID号板子所有全色灯的颜色及亮度  具体解释见函数定义处
fullcolorled_state(id=0,state=1)    //控制对应ID板子  LED闪烁样式  state = 1-3
fullcolor_set_id(id=0,id_new=1)     //改变全色灯板子ID 

modified by MrWang_tju 12.05
全色灯板 灯的数量变为6个  控制方式改变
函数变更为：
fullcolor_get_current(id=0)     //返回通过对应ID板子的电流值,触地状态   id=0x78（传感器广播号） 时 可读取板子ID
fullcolor_readfalshall(id = 0)
fullcolor_readfalsh(id = 0,num = 1)
fullcolor_ledcolor(id=0,sort=1,red=100,green=100,blue=100,ch=1)
fullcolor_flashinit(id=0)
fullcolor_writeflash(id=0,sort=1,value=1)
fullcolor_ledstate(id=0, sort=1, state = 1)
fullcolor_ledstateall(id=0, state = 1,duratime=0,frequency = 0)
fullcolor_set_id(id=0,id_new=1)

modified by liucuicui 12.20
全色灯板 灯的数量变为6个  控制方式不改变
函数名称变更为：
fullcolor_get_current(id=0)-->>>get_current()     //返回通过对应ID板子的电流值,触地状态   id=0x78（传感器广播号） 时 可读取板子ID
fullcolor_readfalshall(id = 0)-->>>read_curref()
fullcolor_readfalsh(id = 0,num = 1)-->>>read_flash
fullcolor_ledcolor(id=0,sort=1,red=100,green=100,blue=100,ch=1)-->>>set_ledcolor()
fullcolor_flashinit(id=0)-->>>flash_init()
fullcolor_writeflash(id=0,sort=1,value=1)-->>>write_flash()
fullcolor_ledstate(id=0, sort=1, state = 1)-->>>set_led()
fullcolor_ledstateall(id=0, state = 1,duratime=0,frequency = 0)-->>>set_leds()
fullcolor_set_id(id=0,id_new=1)-->>>set_id()

modified by liucuicui 2019.1.15
全色灯板 灯的数量变为6个  控制方式不改变
read_flash()flash表修改，read_ledcol()新增，set_leds()修改，read_runpara()新增，set_time()新增

"""


def baudrate_init(baud=19200):
    uart.baudrate = baud


def write_data(data=[], r_n=0):
    baudrate_init(115200)
    check = 0
    num = len(data)
    if num >= 2:
        data[num - 2] = 0
        for i in range(num - 2):
            check += data[i + 1]
        data[num - 2] = check % 100
        uart.write(data)
    else:
        print("待发送的数据有误！")
    if r_n == 0:  # 如果不需要接收数据，则直接恢复默认串口总线波特率
        baudrate_init()


def read_data(num=16):
    i = 100  # 经过测试，发现正常接收16位耗时大概为500，这里设置1000用来保证数据接收完成
    byte_list = []
    n_s = True
    while uart.inWaiting() < num and i > 0:  # To do:
        i -= 1
        if uart.inWaiting() > 0 and n_s:
            if list(uart.read(1))[0] == 123:
                n_s = False
                byte_list.append(123)
    while uart.inWaiting() > 0:
        byte_list.append(list(uart.read(1))[0])
    if len(byte_list) == num:
        baudrate_init()
        return byte_list
    else:
        print("接收的数据有误:")
        print(byte_list)
        baudrate_init()
        return []


def get_current(id=0):
    """function:
        全色灯电流读取模块
        读取通过模块的电流大小，返回当前电流的ADC值，返回机器人触地状态

        Args:
            id:需要读取的模块ID号
        Returns:

        """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x01
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 0
    data[10] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id = byte_list[1]
            type = byte_list[2]
            curr = byte_list[4]*255 + byte_list[3]
            print("ID为", id, "通过电流ADC值为", curr)
            Adc_state = byte_list[5]
            if Adc_state == 1:
                print("ID为", id, "的模块触地")
            elif Adc_state == 0:
                print("ID为", id, "的模块未触地")
            return curr
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False
    #baudrate_init()


def read_curref(id = 0):
    """function:
        全色灯电流读取模块

        读取通过模块的FLASH表内容中的CurrentReference  //电流ADC参考值

        Args:
            id:需要读取的模块ID号
        Returns:

        """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x04
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 0
    # data[8] = (data[1] + data[2] + data[3] + data[4] + data[5]+data[6]+data[7]) % 100
    data[10] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id = byte_list[1]
            type = byte_list[2]
            curr = byte_list[3] * 255 + byte_list[4]
            print("ID为", id, "电流参考ADC值为", curr)
            return curr
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False
    # uart = pyb.UART(2, 19200)  # 选用2号串口作为总线控制串口
    # baudrate_init()


def read_flash(id =0, num=1):
    """function:
        全色灯电流读取模块

        读取通过模块的FLASH表某一位内容

        Address	        Item	                初始值
            01	        ID	                    0x00
            02	        BOARD_TYPE	            0x40
            03	        CurrRef触地状态	        0x03E8
            04	        initMode上电初始模式	0x78
            05          呼吸灯切换时间,单位10ms 0x05
            06	        单向流水灯切换时间      0x0A
            07	        双向流水灯切换时间	    0x0A
            08	        闪烁模式切换时间	    0x1E
            09	        Free1预留1	            0x00
            10	        Free2预留2              0x00
            11	        Led1Red	                0x64
            12	        Led1Green	            0x00
            13	        LED1Blue	            0x00
            14	        Led2Red	                0x64
            15	        Led2Green	            0x00
            16	        LED2Blue	            0x00
            17	        Led3Red	                0x64
            18	        Led3Green	            0x00
            19	        LED3Blue	            0x00
            20	        Led4Red	                0x64
            21	        Led4Green	            0x00
            22	        LED4Blue	            0x00
            23	        Led5Red	                0x64
            24	        Led5Green	            0x00
            25	        LED5Blue	            0x00
            26	        Led6Red	                0x64
            27	        Led6Green	            0x00
            28	        LED6Blue	            0x00
            29	        HardWare Version	    0x02
            30	        SoftWare Version        0x10

        { ID Type Data1  Data2 0 Check }
        Value = Data1*255+Data2

        Args:
            id:需要读取的模块ID号
            num:flash 地址
        Returns:

        """
    #send_data()
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x06
    if num>=1:
        data[4] = num
    else:
        print("地址错误")
        return False
    data[5] = 0
    data[6] = 0
    data[7] = 0
    data[10] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id = byte_list[1]
            flash_data = byte_list[3] * 255 + byte_list[4]
            items_value = ['BOARD_ID', 'Type', '触地状态', '初始模式', '呼吸灯切换时间', '单向流水灯切换时间', '双向流水灯切换时间',
                           '闪烁切换时间', '预留1', '预留2', 'led1RED', 'led1GREEN', 'led1BLUE', 'led2RED', 'led2GREEN',
                           'led2BLUE', 'led3RED', 'led3GREEN', 'led3BLUE', 'led4RED', 'led4GREEN', 'led4BLUE',
                           'led5RED', 'led5GREEN', 'led5BLUE', 'led6RED', 'led6GREEN', 'led6BLUE',
                           'HardWare Version', 'SoftWare Version']
            print(str(id) + "号的" + items_value[num-1] + "为" + str(flash_data))
            return flash_data
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False
    # baudrate_init()


def read_ledcol(id=0, num=1):
    """
    读取当前灯的颜色值

    :param id: 要读取的模块ID号
    :param num:要读取的该模块的灯标号
    :return:
    """
    #send_data()
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x08
    if num >=1 and num <=6:
        data[4] = num
    else:
        print("灯序号超范围（1-6）")
        return False
    data[5] = 0
    data[6] = 0
    data[7] = 0
    # data[8] = (data[1] + data[2] + data[3] + data[4] + data[5]+data[6]+data[7]) % 100
    data[10] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id = byte_list[1]
            led_num = byte_list[2]
            red_value = byte_list[3]
            green_value = byte_list[4]
            blue_value = byte_list[5]
            print(str(id) + "号的第" + str(led_num) + "个灯的颜色值为"+ "红" + str(red_value) + "绿" + str(green_value) + "蓝" + str(blue_value))
            return red_value, green_value, blue_value
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False
    # baudrate_init()


def read_runpara(id =0, ch=1):
    """
    回读运行参数   时间、当前状态等

    Args:
        id:需要读取的模块ID号
        ch:返回运行参数  取值范围（1，2）
            ch == 1 :要读取时间参数
            ch == 2 :要读取当前模式

        Returns:
            返回数据格式{ ID Type CmdData1  Data1  Data2 Check }
	        返回数据算法   para = Data1*255+ Data2
            当 ch =1 时：
                para == 0，始终保持该状态
                para == 1，时间执行完毕
                para >1 ，当前执行剩余时间ms
            当 ch =2 时：
                para == 0:全灭
                para == 1:全亮
                para == 2:呼吸灯
                para == 3:流水灯1
                para == 4:流水灯2
                para == 5:闪烁
                para == 5:自由模式
    """
    #send_data()
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x07
    data[4] = ch
    data[5] = 0
    data[6] = 0
    data[7] = 0
    # data[8] = (data[1] + data[2] + data[3] + data[4] + data[5]+data[6]+data[7]) % 100
    data[10] = 125
    write_data(data, r_n=1)
    byte_list = read_data(8)
    print(byte_list)
    data = byte_list
    if len(byte_list) >= 8:
        ca = (data[1] + data[2] + data[3] + data[4] + data[5]) % 100
        if byte_list[6] == ca and byte_list[0] == 123:
            id = byte_list[1]
            type = byte_list[2]
            para = byte_list[4]*255+byte_list[5]
            if ch == 1:
                if para == 0:
                    print(str(id) + "号全色灯模块始终保持当前模式")
                elif para == 1:
                    print(str(id) + "号全色灯模块当前模式结束")
                else:
                    print(str(id) + "号全色灯模块当前模式执行剩余时间"+str(para)+"ms")
                #return para
            elif ch == 2:
                print(str(id) + "号的当前模式为" + str(para))
            return para
        else:
            print("返回的数据校验失败")
            return False
    else:
        print(byte_list)
        print("返回的数据位数不够!")
        return False
    #baudrate_init()


def set_ledcolor(id=0, sort=1, red=100, green=100, blue=100):
    """function:
    全色灯电流读取模块LED控制

    id   :全色灯电流模块的ID
    sort :取值范围 1-6 ， 代表led 1-6（每个模块上6个led）
    red  :RGB R值
    green:RGB G值
    blue :RGB B值   (灯的颜色及亮度通过RGB值控制， R G B取值范围为0-255， 三种颜色的相对值不同决定最后颜色的差别，
                       RGB值的绝对大小代表灯的亮度不同。)

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x11
    data[4] = sort
    data[5] = red
    data[6] = green
    data[7] = blue
    data[8] = 0
    # data[8] = (data[1] + data[2] + data[3] + data[4] + data[5]+data[6]+data[7]) % 100
    data[10] = 125
    write_data(data)
    # baudrate_init()


def flash_init(id=0):
    """function:
    全色灯电流读取模块LED控制

    id:需要读取的模块ID号

    将FLASH设定为默认值
        Address	        Item	                初始值
            01	        ID	                    0x00
            02	        BOARD_TYPE	            0x40
            03	        CurrRef触地状态	        0x03E8
            05	        initMode上电初始模式	0x78
            05          呼吸灯切换时间,单位10ms 0x05
            06	        单向流水灯切换时间      0x0A
            07	        双向流水灯切换时间	    0x0A
            08	        闪烁模式切换时间	    0x1E
            09	        Free1预留1	            0x00
            10	        Free2预留2              0x00
            11	        Led1Red	                0x64
            12	        Led1Green	            0x00
            13	        LED1Blue	            0x00
            14	        Led2Red	                0x64
            15	        Led2Green	            0x00
            16	        LED2Blue	            0x00
            17	        Led3Red	                0x64
            18	        Led3Green	            0x00
            19	        LED3Blue	            0x00
            20	        Led4Red	                0x64
            21	        Led4Green	            0x00
            22	        LED4Blue	            0x00
            23	        Led5Red	                0x64
            24	        Led5Green	            0x00
            25	        LED5Blue	            0x00
            26	        Led6Red	                0x64
            27	        Led6Green	            0x00
            28	        LED6Blue	            0x00
            29	        HardWare Version	    0x02
            30	        SoftWare Version        0x10

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x05
    data[4] = 0
    data[5] = 0
    data[6] = 0
    data[7] = 0
    data[8] = 0
    data[10] = 125
    write_data(data)
    # baudrate_init()


def write_flash(id=0, addr=1, value=1):
    """function:
    全色灯电流读取模块  写FLASH
    id   :全色灯电流模块的ID
    addr :为FLASH地址
    value:为FLASH对应编号的新值

    FLASH  表
        Address	        Item	                初始值
            01	        ID	                    0x00
            02	        BOARD_TYPE	            0x40
            03	        CurrRef触地状态	        0x03E8
            05	        initMode上电初始模式	0x78
            05          呼吸灯切换时间,单位10ms 0x05
            06	        单向流水灯切换时间      0x0A
            07	        双向流水灯切换时间	    0x0A
            08	        闪烁模式切换时间	    0x1E
            09	        Free1预留1	            0x00
            10	        Free2预留2              0x00
            11	        Led1Red	                0x64
            12	        Led1Green	            0x00
            13	        LED1Blue	            0x00
            14	        Led2Red	                0x64
            15	        Led2Green	            0x00
            16	        LED2Blue	            0x00
            17	        Led3Red	                0x64
            18	        Led3Green	            0x00
            19	        LED3Blue	            0x00
            20	        Led4Red	                0x64
            21	        Led4Green	            0x00
            22	        LED4Blue	            0x00
            23	        Led5Red	                0x64
            24	        Led5Green	            0x00
            25	        LED5Blue	            0x00
            26	        Led6Red	                0x64
            27	        Led6Green	            0x00
            28	        LED6Blue	            0x00
            29	        HardWare Version	    0x02
            30	        SoftWare Version        0x10

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x03
    data[4] = addr
    data[5] = value // 100
    data[6] = value % 100
    data[7] = 0
    data[8] = 0
    data[10] = 125
    write_data(data)
    # baudrate_init()


def set_led(id=0, sort=1, state=1):
    """function:
        全色灯电流读取模块LED控制，控制单个led状态(开、关)

        id   :全色灯电流模块的ID
        sort :为灯的编号（1-6）
        state:控制灯的状态  只有两种  1  常开  0 关闭

        """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x12
    data[4] = sort
    data[5] = state
    data[6] = 0
    data[7] = 0
    data[8] = 0
    data[10] = 125
    write_data(data)
    # baudrate_init()


def set_leds(id=0, state=1):
    """function:
        全色灯电流读取模块LED控制，控制该模块所有led状态

        id   :全色灯电流模块的ID
        state:控制该模块所有灯的状态
            其中     state=0   	全灭
                          =1	全亮
                          =2	呼吸灯（呼吸灯时间及周期可以根据CmdData3 与 CmdData4设置）
                          =3	流水灯样式1
                          =4	流水灯样式2
                          =5	闪烁
                          =6	自由模式
        """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x16
    data[4] = 1
    data[5] = state
    data[6] = 0
    data[7] = 0
    data[8] = 0
    data[10] = 125
    write_data(data)
    # baudrate_init()


def set_time(id=0, duratime=0):
    """function:
    全色灯电流读取模块LED控制，控制该模块全色LED灯 --》状态执行时间

    id          :全色灯电流模块的ID
    duratime    :控制灯  当前状态的持续时间，时间到变为全灭  单位s

    """
    data = [0, 0, 13, 50, 0, 1, 0, 0, 0, 0, 0]
    data[0] = 123
    data[1] = id
    data[2] = 0x40
    data[3] = 0x21
    data[4] = duratime
    data[5] = 0
    data[6] = 0
    data[7] = 0
    data[8] = 0
    data[10] = 125
    write_data(data)
    # baudrate_init()


def set_id(id=0, id_new=1):
    """function:
    全色灯电流读取模块ID 号设置
        id :全色灯电流模块的ID
    """
    write_flash(id, 1, id_new)

