from django.urls import path
from . import views

urlpatterns = [
    path('home/',views.home,name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('survey/', views.survey, name='survey'),
    path('bdisurvey/', views.bdisurvey, name='bdisurvey')
]