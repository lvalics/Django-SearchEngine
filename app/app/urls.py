"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# app/app/urls.py : Main urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from api import urls as app_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api-auth/", include("rest_framework.urls")
    ),  # http://127.0.0.1:8000/api-auth/
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path(
        "api/schema/", SpectacularAPIView.as_view(), name="schema"
    ),  # http://127.0.0.1:8000/api/schema/
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),  # http://127.0.0.1:8000/api/docs/
    path("api/", include(app_urls)),  # http://127.0.0.1:8000/api/
    path("", RedirectView.as_view(url="/api/", permanent=False)),
    path("pdf-ocr-api/", include("pdfocrapi.urls")),
]
