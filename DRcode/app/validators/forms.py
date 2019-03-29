from wtforms import StringField, IntegerField, FloatField
from wtforms.validators import DataRequired, length, Regexp, EqualTo
from DRcode.app.libs.enums import InstructTypeEnum
from DRcode.app.validators.base import BaseForm as Form


class PasswordForm(Form):
    nickname = StringField(validators=[DataRequired(),
                                       length(min=1, max=22)])
    secret = StringField('Password', validators=[
        DataRequired(),
        EqualTo('secret2', message='Password must match.')])
    secret2 = StringField('Confirm password', validators=[DataRequired()])


class TokenForm(Form):
    nickname = StringField(validators=[DataRequired(),
                                       length(min=2, max=22)])
    secret = StringField('Password', validators=[
        DataRequired()])


class TokenInfoForm(Form):
    token = StringField(validators=[DataRequired()])


class ActionForm(Form):
    name = StringField(validators=[])
    body = StringField(validators=[])


class CodeForm(Form):
    name = StringField(validators=[])
    body = StringField(validators=[])


class InstructForm(Form):
    instruct_type = IntegerField(validators=[DataRequired()])
    para1 = StringField()
    para2 = IntegerField()

    def validate_instruct_type(self, value):
        try:
            instruct = InstructTypeEnum(value.data)
        except ValueError as e:
            raise e
        self.instruct_type.data = instruct


class FrameForm(Form):
    instruct_type = IntegerField(validators=[DataRequired()])
    para1 = StringField()
    para2 = IntegerField()

    def validate_frame_type(self, value):
        try:
            instruct = InstructTypeEnum(value.data)
        except ValueError as e:
            raise e
        self.instruct_type.data = instruct


class NetworkForm(Form):
    ssid = StringField(validators=[DataRequired()])
    secret = StringField(validators=[DataRequired()])
