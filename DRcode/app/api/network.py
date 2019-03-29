#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import jsonify
from DRcode.app.libs.redprint import Redprint
from DRcode.app.libs.token_auth import auth
from DRcode.app.libs.error_code import Success, InstructFailed, InstructSuccess
from DRcode.app.validators.forms import NetworkForm

api = Redprint('network')


@api.route('')
def get_network_list():
    from DRcode.app.libs.robot import Robot
    network_list = Robot.robot_get_network_list()
    if network_list:
        return jsonify(network_list), 200
    else:
        return InstructFailed(msg='add network failed')


@api.route('', methods=['POST'])
# @auth.login_required
def add_network():
    from DRcode.app.libs.robot import Robot
    form = NetworkForm().validate_for_api()
    new_ssid = form.ssid.data
    new_password = form.secret.data
    try:
        # 判断需要添加的网络是不是新的网络
        bk_flag, netid = Robot().robot_if_backup(new_ssid)
        # 是新的网络则直接添加
        if bk_flag:
            Robot.robot_network_backup()
            if netid is not None:
                print('exist network----------------------')
                Robot.robot_delete_network(netid)
            else:
                print('new network----------------------')
            if Robot.robot_add_network(new_ssid, new_password):
                print('add network successfully')
                Robot.robot_delete_backup()
                return Success(msg='add network successfully, please restart to take effect')
            else:
                Robot.robot_network_restore()
                print('add network failed')
                Robot.robot_delete_backup()
                return InstructFailed(msg='add network failed')
        else:
            print('This wifi cannot be modified-----------')
            return InstructFailed(msg='This wifi cannot be modified')
    except Exception as result:
        raise InstructFailed(msg='add network failed:{}'.format(result))


# @api.route('', methods=['DELETE'])
# # @auth.login_required
# def remove_network():
#     from DRcode.app.libs.robot import Robot
#     try:
#         Robot().robot_delete_network()
#         return InstructSuccess(msg='delete network failed')
#     except Exception as result:
#         raise InstructFailed(msg='delete network failed:{}'.format(result))
