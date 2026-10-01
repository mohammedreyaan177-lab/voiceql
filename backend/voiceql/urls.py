from django.urls import path
from .views import *

urlpatterns = [
    path('', health),
    path('ask', ask_ai),
    path('voice', voice_query)
]