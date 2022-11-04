from django.urls import path, include
from rest_framework import routers
from .views import whois, dig

app_name = 'api'

# router_v1 = routers.DefaultRouter()
# router_v1.register(r'whois', whois, basename='whois')
# # router_v1.register(r'dig', ..., basename='dig')
#
# urlpatterns = [
#     path('v1/', include(router_v1.urls)),
# ]

urlpatterns = [
    path('v1/whois/', whois),
    path('v1/dig/', dig),
]