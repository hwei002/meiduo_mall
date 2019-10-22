import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CartSerializer

# Create your views here.


class CartView(APIView):
    """
    购物车
    """
    def perform_authentication(self, request):
        """重写检查JWT token是否正确"""
        pass

    def post(self, request):
        """保存购物车数据"""
        # 检查前端发送的数据是否正确
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 判断用户是否登录
        try:
            user = request.user
        except Exception:
            # 前端携带了错误的 JWT  用户未登录
            user = None

        # 保存购物车数据
        if user is not None and user.is_authenticated:
            # 用户已登录 保存到redis中
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            # 购物车数据  hash
            pl.hincrby('cart_%s' % user.id, sku_id, count)

            # 勾选
            if selected:
                pl.sadd('cart_selected_%s' % user.id,  sku_id)

            pl.execute()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登录，保存到cookie中
            # 尝试从cookie中读取购物车数据
            cart_str = request.COOKIES.get('cart')

            if cart_str:

                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            # {
            #     sku_id: {
            #                 "count": xxx, // 数量
            #     "selected": True // 是否勾选
            # },
            # sku_id: {
            #     "count": xxx,
            #     "selected": False
            # },
            # ...
            # }

            # 如果有相同商品，求和
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 返回

            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie('cart', cookie_cart)

            return response


    # def get(self):
    #
    # def put(self):
    #
    # def delete(self):



