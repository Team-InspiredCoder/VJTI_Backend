from rest_framework.serializers import ModelSerializer
from app.models import *



# CustomUser model serializer
class GetCustomUserSerializer(ModelSerializer):

    class Meta:
        model = CustomUser
        exclude = ('password', 'is_active', 'is_staff', 'is_superuser', 'email_verified_at', 'user_permissions', 'groups')




from .models import *
from rest_framework import serializers




class InvoiceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceDetail
        exclude = ('price_id',)


class UserPaymentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPaymentInfo
        exclude = ('stripe_payment_method_response', 'stripe_payment_method_id', 'cvv_no')


class PostUserPaymentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPaymentInfo
        fields = '__all__'


class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        exclude = ('payment_response',)


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packages
        exclude = ('product_id', 'price_id')


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        exclude = ('stripe_subscription_response', 'stripe_customer_id')

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = '__all__'





