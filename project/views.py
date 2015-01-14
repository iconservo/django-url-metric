from django.http import HttpResponse
from django.views.generic import View

__author__ = 'margus'

class TestingView(View):
    def get(self, request):
        return HttpResponse('GET')

    def post(self, request):
        return HttpResponse('POST')

    def put(self, request):
        return HttpResponse('PUT')