from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    # Inscription / Connexion personnalisees (retournent JWT)
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),

    # Endpoints JWT standards
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
