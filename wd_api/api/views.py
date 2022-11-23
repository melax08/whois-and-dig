from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import sys
sys.path.append('../../whois-and-dig')

import whois

from .serializers import WhoisSerializer, DigSerializer
from wd import Domain
from exceptions import BadDomain


class Whois(APIView):
    def post(self, request):
        serializer = WhoisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.data.get('domain')
        try:
            dom = Domain(domain)
            whois_output = dom.whois_json()
        except BadDomain:
            return Response(
                {
                    'result': False,
                    'domain': 'Bad domain'
                },
                status=status.HTTP_200_OK
            )
        except (
                whois.exceptions.WhoisCommandFailed,
                whois.exceptions.WhoisPrivateRegistry,
                whois.exceptions.FailedParsingWhoisOutput,
                whois.exceptions.UnknownTld,
                whois.exceptions.UnknownDateFormat
        ) as error:
            return Response(
                {
                    'result': False,
                    'domain': str(error)
                 },
                status=status.HTTP_200_OK
            )
        return Response(whois_output, status=status.HTTP_200_OK)


class Dig(APIView):
    def post(self, request):
        serializer = DigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain = serializer.data.get('domain')
        record = serializer.data.get('record')
        custom_dns = serializer.data.get('dns')
        try:
            dom = Domain(domain)
            dig_output = dom.dig(record, custom_dns)
        except BadDomain:
            return Response(
                {
                    'result': False,
                    'domain': 'Bad domain'
                },
                status=status.HTTP_200_OK
            )
        return Response(dig_output, status=status.HTTP_200_OK)
