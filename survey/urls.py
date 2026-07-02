from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 👈 THIS LINE FIXES EVERYTHING
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),

    path('survey/', views.survey, name='survey'),
    path('bdisurvey/', views.bdisurvey, name='bdisurvey'),

    path('chatbot/', views.chatbot, name='chatbot'),
    path('consultation/', views.consultation, name='consultation'),
    path('analytics/', views.analytics, name='analytics'),
]