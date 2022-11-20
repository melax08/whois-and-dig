from django.urls import path
from rest_framework.authtoken import views

from .views import Whois, Dig

app_name = 'api'

urlpatterns = [
    path('v1/whois/', Whois.as_view()),
    path('v1/dig/', Dig.as_view()),
    path('v1/get-token/', views.obtain_auth_token)
]