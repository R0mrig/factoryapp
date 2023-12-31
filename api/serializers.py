from rest_framework import serializers
from database.models import User
from database.models import UserSource, User



## serializer pour l'API user creation ##

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'company']  # Tu peux choisir les champs que tu veux inclure.

## serializer pour l'API user_source creation ##

class UserSourceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = UserSource
        fields = ['user_email', 'competitors', 'linkedin', 'references', 'youtube']

    def create(self, validated_data):
        user_email = validated_data.pop('user_email', None)
        if user_email:
            user, created = User.objects.get_or_create(email=user_email)
            validated_data['user'] = user
        user_source = UserSource.objects.create(**validated_data)
        return user_source