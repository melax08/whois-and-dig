from django.urls import path
from rest_framework.authtoken import views

from .views import whois, dig

app_name = 'api'

urlpatterns = [
    path('v1/whois/', whois),
    path('v1/dig/', dig),
    path('v1/get-token/', views.obtain_auth_token)
]