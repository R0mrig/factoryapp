from django.urls import path
from . import views



urlpatterns = [
    path("",views.User),
    path('users/', views.user_list_create, name='user-list-create'),
    path('user-sources/', views.user_sources, name='user-sources'),

]