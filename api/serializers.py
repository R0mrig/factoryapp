from rest_framework import serializers
from database.models import User
from database.models import UserSource, User
from database.models import Article




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
        fields = ['title', 'base_content', 'content', 'user_comment', 'tone_of_voice', 'content_goal', 'language']

    def create(self, validated_data):
        user_email = validated_data.pop('user_email', None)
        if user_email:
            user, created = User.objects.get_or_create(email=user_email)
            validated_data['user'] = user
        user_source = UserSource.objects.create(**validated_data)
        return user_source
    


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['title', 'base_content', 'content', 'tone_of_voice', 'content_goal', 'language', 'user_comment', 'content_size', 'goals']


class TrendSerializer(serializers.Serializer):
    titre = serializers.CharField(max_length=300)
    base_content = serializers.CharField(max_length=1500)