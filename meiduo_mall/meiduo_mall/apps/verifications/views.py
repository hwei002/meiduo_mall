import random

from django.http.response import HttpResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView

from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms_code
from . import serializers
from . import constants


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        # 生成验证码图片
        _, text, image = captcha.generate_captcha()  # 返回3个参数！！！

        # 获取redis的连接对象
        # 调get_redis_connection方法传递redis配置名称获取redis连接对象，用redis连接对象执行redis命令
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="images/jpg")


class SMSCodeView(GenericAPIView):
    serializer_class = serializers.CheckImageCodeSerializer

    def get(self, request, mobile):
        """
        创建短信验证码
        """
        # 判断图片验证码, 判断是否在60s内
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # 生成短信验证码
        sms_code = "%06d" % random.randint(0, 999999)

        # 保存短信验证码与发送记录
        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()  # 使用redis的管道收集命令【一次性传递多个命令，减少与数据库的连接次数】
        pl.multi()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 发送短信验证码
        # sms_code_expires = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        # ccp = CCP()
        # ccp.send_template_sms(mobile, [sms_code, sms_code_expires], constants.SMS_CODE_TEMP_ID)

        # 使用celery完成发送短信的异步任务
        send_sms_code.delay(mobile, sms_code)

        return Response({"message": "OK"})


