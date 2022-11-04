from rest_framework import status
from rest_framework.response import Response
from .serializers import WhoisSerializer, DigSerializer
from rest_framework.decorators import api_view
import sys
sys.path.append('../../whois-and-dig')

from wd import Domain
from exceptions import BadDomain


@api_view(['POST'])
def whois(request):
    serializer = WhoisSerializer(data=request.data)
    if serializer.is_valid():
        domain = serializer.data['domain']
        try:
            dom = Domain(domain)
            whois_output = dom.whois_json()
        except BadDomain:
            return Response({'message': 'Bad domain'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(whois_output, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def dig(request):
    serializers = DigSerializer(data=request.data)
    if serializers.is_valid():
        domain = serializers.data.get('domain')
        record = serializers.data.get('record')
        custom_dns = serializers.data.get('dns')
        try:
            dom = Domain(domain)
            dig_output = dom.dig(record, custom_dns)
        except BadDomain:
            return Response({'message': 'Bad domain'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(dig_output, status=status.HTTP_200_OK)
    return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
