from django_redis import get_redis_connection
from redis.exceptions import RedisError
from rest_framework import serializers
import logging
logger = logging.getLogger('django')  # 获取日志记录器


class CheckImageCodeSerializer(serializers.Serializer):
    """
    图片验证码校验序列化器
    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        """
        校验
        """
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        # 查询真实图片验证码
        redis_conn = get_redis_connection('verify_codes')
        real_image_code_text = redis_conn.get('img_%s' % image_code_id)
        if not real_image_code_text:
            raise serializers.ValidationError('图片验证码无效')

        # 删除图片验证码，防止用户对同一个图片验证码进行多次请求验证
        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        # 比较图片验证码
        real_image_code_text = real_image_code_text.decode()
        if real_image_code_text.lower() != text.lower():
            raise serializers.ValidationError('图片验证码错误')

        # 判断上一次发送，是否在 60s 内，由redis维护60秒有效期。
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')

        return attrs


