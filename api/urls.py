from django.urls import path
from . import views
from .views import (
    user_list_create, 
    user_sources, 
    create_article, 
    suggest_for_trends, 
    suggest_for_tailor_content, 
    CustomTokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path("", views.User),
    path('users/', user_list_create, name='user-list-create'),
    path('user-sources/', user_sources, name='user-sources'),
    path('create_article/', create_article),
    path('suggest_for_trends/', suggest_for_trends),
    path('suggest_for_tailor_content/', suggest_for_tailor_content),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
