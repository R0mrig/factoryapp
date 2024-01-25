from django.urls import path
from . import views
from .views import create_article
from .views import suggest_for_trends 
from .views import suggest_for_tailor_content 



urlpatterns = [
    path("",views.User),
    path('users/', views.user_list_create, name='user-list-create'),
    path('user-sources/', views.user_sources, name='user-sources'),
    path('create_article/', create_article),
    path('suggest_for_trends/', suggest_for_trends),
    path('suggest_for_tailor_content/', suggest_for_tailor_content),
]