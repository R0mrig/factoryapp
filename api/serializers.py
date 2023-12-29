from rest_framework import serializers
from database.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'company']  # Tu peux choisir les champs que tu veux inclure.
