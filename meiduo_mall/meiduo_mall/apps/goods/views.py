from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin

from .serializers import SKUSerializer
from .models import SKU
from . import constants

# Create your views here.


class HotSKUListView(ListCacheResponseMixin, ListAPIView):
    """返回热销数据
    /categories/(?P<category_id>\d+)/hotskus/
    """
    serializer_class = SKUSerializer

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:constants.HOT_SKUS_COUNT_LIMIT]

