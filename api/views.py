from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from database.models import User
from database.models import UserSource
from .serializers import UserSerializer
from .serializers import UserSourceSerializer




@api_view(['GET', 'POST'])
def user_list_create(request):
    if request.method == 'GET':
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
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
