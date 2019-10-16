import logging
logger = logging.getLogger("django")

from .yuntongxun.sms import CCP
from .constants import SMS_CODE_REDIS_EXPIRES, SMS_CODE_TEMP_ID
from celery_tasks.main import app


@app.task(name='send_sms_code')
def send_sms_code(mobile, code):
    """
    发送短信验证码
    :param mobile: 手机号
    :param code: 验证码
    :param expires: 有效期
    :return: None
    """
    try:
        ccp = CCP()
        sms_code_expires = str(SMS_CODE_REDIS_EXPIRES // 60)
        result = ccp.send_template_sms(mobile, [code, sms_code_expires], SMS_CODE_TEMP_ID)
    except Exception as e:
        logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
    else:
        if result == 0:
            logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)


