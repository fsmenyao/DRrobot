from flask import Blueprint
from DRcode.app.api import codes, actions, password, \
    states, instructs, network, token, camera, output, update


def create_blueprint():
    bp = Blueprint('v0', __name__)

    codes.api.register(bp)
    actions.api.register(bp)
    password.api.register(bp)
    states.api.register(bp)
    network.api.register(bp)
    instructs.api.register(bp)
    token.api.register(bp)
    camera.api.register(bp)
    output.api.register(bp)
    update.api.register(bp)

    return bp
