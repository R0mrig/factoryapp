from django.urls import path
from . import views
from .views import (
    sign_up,
    user_list_create,
    execute_trends, 
    user_sources, 
    create_article, 
    suggest_for_trends, 
    suggest_for_tailor_content, 
    CustomTokenObtainPairView,
    TokenRefreshView,
    TokenCreateView,
    linkedin_post_create
)

urlpatterns = [
    path("", views.User),
    path('users/', user_list_create, name='user-list-create'),
    path('user-sources/', user_sources, name='user-sources'),
    path('execute_trends/', execute_trends, name='execute_trends'),
    path('create_article/', create_article),
    path('suggest_for_trends/', suggest_for_trends),
    path('suggest_for_tailor_content/', suggest_for_tailor_content),
    path('api/token/', TokenCreateView.as_view(), name='token_create'),  # Ajoutez ce chemin pour la génération de token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('sign-up/', sign_up, name='sign-up'),
    path('api/linkedin_post/', linkedin_post_create, name='linkedin_post_create'),

]
