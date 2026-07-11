from django.urls import include, path

urlpatterns = [
    path("auth/", include("nomadicode_auth.urls")),
    path("accounts/", include("allauth.urls")),
]
