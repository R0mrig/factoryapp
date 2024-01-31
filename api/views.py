from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate
import subprocess
import json
import requests

from .serializers import (
    UserSerializer, 
    UserSourceSerializer, 
    ArticleSerializer, 
    TrendSerializer, 
    TailorTrendSerializer, 
    CustomTokenObtainPairSerializer
)
from database.models import User, UserSource, Article
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@api_view(['GET', 'POST'])
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Convertir les données validées en JSON
            data_as_json = json.dumps(serializer.validated_data)
            # Exécuter le script generate_content.py avec les données validées
            subprocess.call(["python", "/Users/romain-pro/Desktop/factoryapp/User_setup.py", data_as_json])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated]) 
def user_sources(request):
    if request.method == 'GET':
        email = request.query_params.get('email')
        if email:
            user_sources = UserSource.objects.filter(user__email=email)
            serializer = UserSourceSerializer(user_sources, many=True)
            return Response(serializer.data)
        return Response({'detail': 'Email parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        serializer = UserSourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_article(request):
    serializer = ArticleSerializer(data=request.data)
    if serializer.is_valid():
        # Récupération et stockage des données validées dans un fichier ou une variable
        data = json.dumps({
            "title": serializer.validated_data['title'],
            "base_content": serializer.validated_data.get('base_content', ''),
            "tone_of_voice": serializer.validated_data['tone_of_voice'],
            "content_goal": serializer.validated_data['content_goal'],
            "product": serializer.validated_data['product'],
            "description": serializer.validated_data.get('description', ''),
            "language": serializer.validated_data['language'],
            "user_comment": serializer.validated_data.get('user_comment', ''),
            "content_size": serializer.validated_data['content_size'],
            "goals": serializer.validated_data['goals'],
            "email": serializer.validated_data.get('email', ''),
            "Company_info": serializer.validated_data.get('Company_info', '') 
        })

        # Exécuter le script test.py avec les données validées
        call(["python", "/Users/romain-pro/Desktop/factoryapp/generate_content.py", data])

        # Logique supplémentaire pour confirmer le succès de l'opération
        # ...

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_for_trends(request):
    serializer = TrendSerializer(data=request.data)

    if serializer.is_valid():
        # Ajoutez l'email aux données validées
        validated_data = serializer.validated_data
        validated_data['email'] = serializer.validated_data.get('email', '')

        # Exécuter le script suggest_trends.py avec les données validées
        call(["python", "/Users/romain-pro/Desktop/factoryapp/suggest_trends.py", json.dumps(validated_data)])

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suggest_for_tailor_content(request):
    serializer =  TailorTrendSerializer(data=request.data)

    if serializer.is_valid():
        # Ajoutez l'email aux données validées
        validated_data = serializer.validated_data
        validated_data['email'] = serializer.validated_data.get('email', '')

        # Exécuter le script suggest_trends.py avec les données validées
        call(["python", "/Users/romain-pro/Desktop/factoryapp/Tailor_trends.py", json.dumps(validated_data)])

        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenRefreshView

class TokenCreateView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(email=request.data['email'], password=request.data['password'])
            if user is not None:
                refresh = RefreshToken.for_user(user)

                webhook_data = {
                    "email": user.email,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }

                webhook_url = 'https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/get_token'
                requests.post(webhook_url, json=webhook_data)

                return Response(serializer.validated_data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    # Si vous avez besoin de personnaliser, ajoutez votre logique ici
    pass
