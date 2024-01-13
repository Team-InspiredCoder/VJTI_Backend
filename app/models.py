from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _


# Create your models here.




class CustomAccountManager(BaseUserManager):

    def create_superuser(self, email, username=None, password=None, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True.')
        if other_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True.')

        return self.create_user(email, username, password, **other_fields)

    def create_user(self, email, username=None, password=None, **other_fields):

        if not email:
            raise ValueError(_('You must provide an email address'))

        if username == None:
            username = email

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **other_fields)

        if password is not None:
            user.set_password(password)

        user.save()
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):

    # this fields are mandatory for all type of users
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    # profile_picture = models.CharField(max_length=256, blank=True, null=True)
    gender = models.CharField(max_length=8, blank=True, null=True)

    # conditional fields
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    two_step_auth = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)

    # payment gateway fields
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_customer_response = models.JSONField(max_length=1000, blank=True, null=True)

    # timestamps
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


    # settings
    objects = CustomAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class UserVerification(models.Model):
    email = models.CharField(max_length=70, blank=True, null=True)
    otp = models.CharField(max_length=10, blank=True, null=True)
    token = models.CharField(unique=True, max_length=200, blank=True, null=True)
    # action => signup | forgotPasword | twoStepAuth | login 
    action = models.CharField(max_length=50, blank=True, null=True)
    otp_expire_on = models.DateTimeField(null=True, blank=True)
    token_expire_on = models.DateTimeField(null=True, blank=True)
    # metadata = models.JSONField(max_length=512, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.email




from django.db import models

from django.db.models.fields.related import ForeignKey, OneToOneField

from app.models import CustomUser


# from analytics.models import *


# Create your models here.

# default payment method key => Done
# create obj payment history


default_prices_json = {"custom":{"amount":"0", "price_id":""}, "pro":{"amount":"0", "price_id":""}, "free":{"amount":"0", "price_id":""}}

# class Packages(models.Model):
#     # user = ForeignKey(NormalUsers, on_delete=models.CASCADE, blank=True, null=True)
#     name = models.CharField(max_length=250)
#     product_id = models.CharField(max_length=500)
#     # mode => one-time | recurring
#     mode = models.CharField(max_length=250)
#     # recurring_period => (in months) & -1 if one-time payment 
#     recurring_period = models.CharField(max_length=10)
#     # prices => {"custom":{"amount":"0", "price_id":""}, "pro":{"amount":"500", "price_id":""}, "free":{"amount":"0", "price_id":""}}
#     prices = models.JSONField(max_length=500, default=default_prices_json, blank=True)


class Packages(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(null=True,blank=True)
    product_id = models.CharField(max_length=500)
    price_id = models.CharField(max_length=500,null=True)
    amount = models.FloatField(null=True,blank=True)
    currency = models.CharField(max_length=20,default="EUR")
    # mode => one-time | recurring
    mode = models.CharField(max_length=250)
    # recurring_period => (in months) & -1 if one-time-payment 
    recurring_period = models.CharField(max_length=10)
    features = models.JSONField(max_length=500, blank=True,null=True)


default_payment_method_json = {"last_id":"0", "payment_methods":{}}

class UserPaymentInfo(models.Model):

    user = ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    # stripe_payment_method_id => {"last_id":"5", "payment_methods":{"1":"payment_method_id",..., "5":"payment_method_id"}}
    # stripe_payment_method_id = models.JSONField(max_length=500, default=default_payment_method_json, blank=True)
    stripe_payment_method_id = models.CharField(max_length=100, blank=True)
    stripe_payment_method_response = models.JSONField(max_length=500, blank=True, null=True)

    ptype = models.CharField(max_length=50, blank=True)
    card_no = models.CharField(max_length=20, blank=True)
    exp_month = models.CharField(max_length=10, blank=True)
    exp_year = models.CharField(max_length=10, blank=True)
    cvv_no = models.CharField(max_length=10, blank=True)

    billing_address = models.TextField(max_length=1000, blank=True, null=True)
    currency = models.CharField(max_length=25, blank=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class InvoiceDetail(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True)

    invoice_file = models.FileField(null=True,blank=True,upload_to='payment/files/invoices/')
    invoice_number = models.CharField(max_length=500, default="0", unique=True)
    
    plan_start_date = models.DateField(null=True,blank=True)
    plan_end_date = models.DateField(null=True,blank=True)
    invoice_date = models.DateField(null=True,blank=True)

    quantity = models.IntegerField(null=True,blank=True)
    sub_total = models.FloatField(null=True,blank=True)
    total = models.FloatField(null=True,blank=True)
    # amount_due = models.DateField(null=True,blank=True)

    price_id = models.CharField(max_length=500, null=True, blank=True)

    user_mobile_no = models.CharField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class PaymentHistory(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, blank=True, null=True)
    package = models.ForeignKey(Packages, on_delete=models.DO_NOTHING, blank=True, null=True)
    invoice = models.ForeignKey(InvoiceDetail, on_delete=models.DO_NOTHING, blank=True, null=True)
    payment_method = models.ForeignKey(UserPaymentInfo, on_delete=models.DO_NOTHING, blank=True, null=True)

    invoice_download_link = models.CharField(max_length=600,null=True,blank=True)

    payment_type = models.CharField(max_length=100, null=True, blank=True)
    currency = models.CharField(max_length=300,null=True,blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_response = models.JSONField(max_length=2000,null=True,blank=True)
    amount = models.FloatField(null=True, blank=True)

    description = models.CharField(max_length=200, null=True, blank=True) #Payment Description: Ex: Monthly Subscription Renewal

    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class UserSubscription(models.Model):

    user = ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    package = ForeignKey(Packages, on_delete=models.CASCADE, blank=True, null=True)
    subscription_plan = models.CharField(max_length=250, blank=True, null=True)

    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_response = models.JSONField(max_length=500, blank=True, null=True)
    # status => active | canceled | force_stopped
    status = models.CharField(max_length=100, default="active", blank=True)
    # quota => remaining monthly quota according to plan
    quota = models.JSONField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)



class Garage(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    subscriptionEnabled = models.BooleanField(default=False)


class Rating(models.Model):
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE)
    rating = models.IntegerField(null=True, blank=True)
    