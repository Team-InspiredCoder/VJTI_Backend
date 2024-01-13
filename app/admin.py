from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(UserVerification)
admin.site.register(Packages)
admin.site.register(UserPaymentInfo)
admin.site.register(PaymentHistory)
admin.site.register(UserSubscription)
