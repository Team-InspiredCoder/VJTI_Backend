from django.urls import path
from app.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register', Register.as_view(), name="register"),
    path('login', Login.as_view(), name="login"),
    path('verify-user/<str:vmode>', VerifyUser.as_view(), name="verify-user"),
    path('resend-otp', ResendOTP.as_view(), name="resend-otp"),

    # test
    path('link/verify/<str:token>', verifyLink, name="verify-link"),
    path('indian-oil-data/',scrap_from_indian_oil),
]


# add at the last
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
