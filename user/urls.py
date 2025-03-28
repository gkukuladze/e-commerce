"""
URL mappings for the user API.
"""
from django.urls import path

from user import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

app_name = 'user'

# urlpatterns = [
#     path('create/', views.CreateUserView.as_view(), name='create'),
#     path(
#         'api/token/',
#         TokenObtainPairView.as_view(),
#         name='token_obtain_pair'
#     ),
#     path(
#         'api/token/refresh/',
#         TokenRefreshView.as_view(),
#         name='token_refresh'
#     ),
#     path('me/', views.ManageUserView.as_view(), name='me'),
#     path('logout/', views.LogoutView.as_view(), name='logout'),
# ]
urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CustomTokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path('logout/', TokenBlacklistView.as_view())
]
