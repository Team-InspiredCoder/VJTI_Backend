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
    # stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    # stripe_customer_response = models.JSONField(max_length=1000, blank=True, null=True)

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






