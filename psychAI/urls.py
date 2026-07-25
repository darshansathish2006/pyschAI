from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.contrib.auth.views import LogoutView

def home(request):
    return HttpResponse("Hello, your Django app is live 🚀")

urlpatterns = [
    path('', include('survey.urls')),
    path('admin/', admin.site.urls),

    path(
        "logout/",
        LogoutView.as_view(next_page="login"),
        name="logout",
    ),
]