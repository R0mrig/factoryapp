from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.contrib.auth import authenticate
import threading
import subprocess
import json
import requests
from subprocess import call


from .serializers import (
    UserSerializer, 
    UserSourceSerializer, 
    ArticleSerializer, 
    TrendSerializer, 
    TailorTrendSerializer, 
    CustomTokenObtainPairSerializer,
    LinkedInPostSerializer,
)

from database.models import User, UserSource, Article, LinkedInPost
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@api_view(['POST'])
def sign_up(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Génération du token
        refresh = RefreshToken.for_user(user)

        # Préparation des données pour le webhook
        webhook_data = {
            "email": user.email,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh)
        }

        # URL du webhook Bubble
        webhook_url = 'https://laurent-60818.bubbleapps.io/version-test/api/1.1/wf/get_token'

        # Envoi des données au webhook
        requests.post(webhook_url, json=webhook_data)

        return Response({'email': user.email, 'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated]) 
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Vérifie si l'utilisateur existe déjà (mise à jour) ou non (création)
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            update = True
        except User.DoesNotExist:
            user = None
            update = False

        serializer = UserSerializer(user, data=request.data, partial=update)
        if serializer.is_valid():
            user = serializer.save()

            # Convertir les données validées en JSON
            data_as_json = json.dumps(serializer.validated_data)

            # Exécuter le script externe avec les données validées
            script_path = "/Users/romain-pro/Desktop/factoryapp/User_setup.py"
            subprocess.call(["python", script_path, data_as_json])

            status_code = status.HTTP_200_OK if update else status.HTTP_201_CREATED
            return Response(serializer.data, status=status_code)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
def user_sources(request):
    if request.method == 'GET':
        email = request.query_params.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                user_sources = UserSource.objects.filter(user=user)
                serializer = UserSourceSerializer(user_sources, many=True)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Email parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        email = request.data.get('email')
        urls = request.data.get('competitors', [])
        
        user, created = User.objects.get_or_create(email=email)
        
        linkedin_urls = [url for url in urls if "linkedin" in url.lower()]
        other_urls = [url for url in urls if "linkedin" not in url.lower()]
        
        # Conversion des listes d'URLs en chaînes de caractères séparées par des virgules
        linkedin_urls_str = ", ".join(linkedin_urls)
        other_urls_str = ", ".join(other_urls)
        
        user_source, created = UserSource.objects.update_or_create(
            user=user,
            defaults={'linkedin': linkedin_urls_str, 'competitors': other_urls_str}
        )
        
        subprocess.call(["python", "/Users/romain-pro/Desktop/factoryapp/LinkedIn_scrap.py", str(user.id)])
        
        subprocess.call(["python", "/Users/romain-pro/Desktop/factoryapp/trends.py", str(user.id)])
        
        return Response({'message': 'URLs processed successfully'}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def execute_trends(request):
    email = request.data.get('email')
    user = get_object_or_404(User, email=email)
    user_id = user.id

    # Exécuter le script trends.py avec l'ID de l'utilisateur
    subprocess.call(["python", "/Users/romain-pro/Desktop/factoryapp/trends.py", str(user_id)])

    return Response({"message": "Trends processing started for user " + email}, status=status.HTTP_200_OK)




@api_view(['POST'])
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
            "Company_info": serializer.validated_data.get('Company_info', '') ,
            "ID_content": serializer.validated_data.get('ID_content', '') 
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


def run_script_in_thread(user_id, post_id):
    script_path = "//Users/romain-pro/Desktop/factoryapp/LinkedInPost_analyse.py"
    subprocess.run(["python", script_path, user_id, post_id])


@api_view(['POST'])
def linkedin_post_create(request):
    serializer = LinkedInPostSerializer(data=request.data)
    if serializer.is_valid():
        linkedin_post = serializer.save()
        user_id = request.data.get('user_id')  # Modification ici pour utiliser l'ID utilisateur depuis le corps de la requête


        # Lancer le script dans un thread séparé
        thread = threading.Thread(target=run_script_in_thread, args=(user_id, str(linkedin_post.id)))
        thread.start()

        return Response({'message': 'Post LinkedIn enregistré avec succès', 'post_id': linkedin_post.id}, status=201)
    else:
        return Response(serializer.errors, status=400)
    
