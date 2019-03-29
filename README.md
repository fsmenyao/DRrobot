# DRrobot

[*本项目的github地址*](https://github.com/fsmenyao/DRrobot)

## 概述

* **机器人Web后端代码**

## 目录

* [概述](#概述)
* [目录](#目录)
* [配置](#配置)
* [使用](#使用)

## 配置

* **硬件环境：*Raspberry Pi Zero W***

  * 配置参考：

    * [*学习笔记-Raspberry Pi Zero W-1：系统安装及SSH和wifi配置（无需显示器）*](https://blog.csdn.net/RambleMY/article/details/81197422)​

    * [*学习笔记-Raspberry Pi Zero W-4：串口（UART）的配置和使用*](https://blog.csdn.net/RambleMY/article/details/81206090)

* **运行环境：Python3**

  * 配置参考：

    * [*学习笔记-Raspberry Pi Zero W-2：Python3下载安装和配置（更换apt-get和pip的镜像源）*](https://blog.csdn.net/RambleMY/article/details/82109788)

    * 依赖库
        ```
        flask
        flask-wtf
        flask-cors
        flask-httpauth
        requests
        ```

* **语音MP3配置**

  * 配置参考
    ```
    安装git:
    sudo apt-get install git
    下载声卡驱动并安装:
    sudo git clone https://github.com/respeaker/seeed-voicecard.git
    cd seeed-voicecard
    sudo ./install.sh
    重启:
    sudo reboot
    百度语音python库安装:
    sudo pip3  install baidu-aip
    ```


*  **其他配置**

    * 项目位置
        ```
        /home/pi/DRrobot
        ```

    * 在树莓派中创建文件夹以保存代码
        ```
        用户不可更改的python代码保存在: /home/pi/DRrobot/DRdata/codes/system
        用户可以更改的python代码保存在: /home/pi/ DRrobot/DRdata/codes/user
        用户不可更改的动作文件(.txt)保存在: /home/pi/ DRrobot/DRdata/actions/system
        用户可以更改的动作文件(.txt)保存在: /home/pi/ DRrobot/DRdata/actions/user
        用户不可更改的音频文件保存在: /home/pi/ DRrobot/DRdata/actions/system
        用户可以更改的t音频文件保存在: /home/pi/ DRrobot/DRdata/actions/user
        ```

    * 将libs的路径加入到python3库文件系统路径中
        ```
        输入命令：
        sudo nano /usr/lib/python3/dist-packages DR.pth
        写入：
        /home/pi/DRrobot/app/libs
        /home/pi/DRrobot
        ```

## 使用

* **启动**

  * 开机自动启动

    * [*学习笔记-Raspberry Pi Zero W-6：启动命令和开机启动*](https://blog.csdn.net/RambleMY/article/details/88552711)

  * 手动启动

        ```
        关闭相关进程：
        sudo killall -9 python3
        启动服务器：
        sudo python3 /home/pi/DRrobot/DRboot.py

        ```

* **调试**

  * 使用*Postman*调试

  * 使用*大然科技.exe*调试
​
