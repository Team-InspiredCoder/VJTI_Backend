from django.urls import path
from app.views import *
from django.conf import settings
from django.conf.urls.static import static
from .stripe_api import *
urlpatterns = [
    path('register', Register.as_view(), name="register"),
    path('login', Login.as_view(), name="login"),
    path('verify-user/<str:vmode>', VerifyUser.as_view(), name="verify-user"),
    path('resend-otp', ResendOTP.as_view(), name="resend-otp"),

    # test
    path('link/verify/<str:token>', verifyLink, name="verify-link"),
    path('indian-oil-data/',scrap_from_indian_oil),
    # path('puc-data/',puc_data),
    path('register-garage/',register_garage),
    path('get-garage/',get_garage),
    path('rate-garage/',rate_garage),

    path('history/crud',PaymentHistoryCRUD.as_view()),
    

    path('subscription/', Subscription.as_view(), name='Subscription'),

    path('methods/', PaymentMethod.as_view(), name='PaymentMethod'),
    path('pay/', Payment.as_view(), name='Payment'),
    path('default/set/', SetDefaultPaymentMethod.as_view(), name='SetDefaultPaymentMethod'),
    path('packages/',PackagesView.as_view(), name='PackagesView'),

    # test urls here
    path('test/', test, name='test'),
    path('generate-invoice/',GenerateInvoice.as_view()),
    path('history/',PaymentHistoryData.as_view()),
]


# add at the last
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
