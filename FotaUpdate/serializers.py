from rest_framework import serializers


class ExeFetchVin(serializers.Serializer):
    vin = serializers.CharField()



