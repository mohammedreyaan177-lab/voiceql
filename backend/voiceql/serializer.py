#Model Serializer
from rest_framework import serializers

from voiceql.models import sales


class salesSerializer(serializers.ModelSerializer):
    class Meta:
        model = sales
        fields = ('id', 'products', 'price')
