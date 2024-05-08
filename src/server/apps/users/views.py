import stripe
from apps.users.api.serializers import RegistrationSerializer, StripeSerializer, UserSerializer
from django.conf import settings
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User

stripe.api_key = settings.STRIPE_SECRET_KEY


class UserRegisterAPIView(APIView):
    serializer_class = RegistrationSerializer

    def post(self, request, *args, **kargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = {
                "success": True,
                "user": serializer.data,
                "token": Token.objects.get(user__id=serializer.data["id"]).key,
            }
            return Response(response, status=status.HTTP_200_OK)
        raise ValidationError(serializer.errors, code=status.HTTP_406_NOT_ACCEPTABLE)


class UserLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args):
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({"success": True, "detail": "Logged out!"}, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CreateSubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StripeSerializer

    def post(self, request, *args, **kargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.data["email"]
            plan_id = serializer.data["plan_id"]

        if not email or not plan_id:
            return Response(
                {"error": "Email and plan_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if customer already exists in Stripe
        existing_customers = stripe.Customer.list(email=email)
        if existing_customers:
            customer_id = existing_customers.data[0].id
        else:
            # Create a new customer in Stripe
            try:
                new_customer = stripe.Customer.create(email=email)
                customer_id = new_customer.id
            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create subscription for the customer
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": plan_id}],
            )
            return Response(
                {"success": True, "subscription_id": subscription.id},
                status=status.HTTP_201_CREATED,
            )
        except stripe.error.StripeError as e:
            # Handle any Stripe errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListProductsAPIView(APIView):
    def get(self, request, format=None):
        try:
            products = stripe.Product.list()
            return Response(products.data, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            # Handle any Stripe errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckoutAPIView(APIView):
    serializer_class = StripeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        try:
            # Get the required parameters from the request data
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                email = serializer.data["email"]
                plan_id = serializer.data["plan_id"]

            if not email or not plan_id:
                return Response(
                    {"error": "Email and product_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Check if customer already exists in Stripe
            existing_customers = stripe.Customer.list(email=email)
            if existing_customers:
                customer_id = existing_customers.data[0].id
            else:
                # Create a new customer in Stripe
                try:
                    new_customer = stripe.Customer.create(email=email)
                    customer_id = new_customer.id
                    user = self.request.user
                    user.stripe_id = customer_id
                    user.save()
                except stripe.error.StripeError as e:
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create a Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": plan_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                success_url="https://yourdomain.com/success/",
                cancel_url="https://yourdomain.com/cancel/",
                customer=customer_id,
            )

            # Return the checkout session ID
            return Response({"checkout_session_id": checkout_session.id}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            # Handle any Stripe errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

