from apps.users.views import (
    CheckoutAPIView,
    CreateSubscriptionAPIView,
    CurrentUserView,
    ListProductsAPIView,
    UserLogoutAPIView,
    UserRegisterAPIView,
)
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("register/", UserRegisterAPIView().as_view(), name="register"),
    path("token/", obtain_auth_token, name="token-auth"),
    path("user/", CurrentUserView().as_view(), name="current_user"),
    path("logout/", UserLogoutAPIView().as_view(), name="logout"),
    path("create-subscription/", CreateSubscriptionAPIView().as_view(), name="create_subscription"),
    path("list-products/", ListProductsAPIView().as_view(), name="list_products"),
    path("checkout/", CheckoutAPIView().as_view(), name="checkout"),
]
