from django.urls import path
from . import views

urlpatterns = [
    path('',views.homePage),
    path('predict',views.getPredict),
    path("simple", views.simple_upload)
]
