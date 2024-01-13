from datetime import datetime
from http.client import HTTPResponse
from importlib.metadata import metadata
from struct import pack
import traceback
# from bson import is_valid
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from app.models import *
from app.serializers import *
from django.views.decorators.csrf import csrf_exempt
from backend import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.template.loader import render_to_string
from io import BytesIO
from pathlib import Path
# from xhtml2pdf import pisa
from django.template.loader import get_template
from rest_framework.decorators import api_view
# import pdfkit
import random
from .serializers import *
from .models import *
from datetime import date
import traceback
import stripe
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives

# Create your views here.


# stripe api key
stripe.api_key = settings.STRIPE_SECRET_KEY

def render_to_pdf(template_src, context, file_name="invoice"):
    file_path = f'payment/files/invoices/{file_name}_{str(random.randint(100000, 9999999))}.pdf'
    template = get_template(template_src)
    html = template.render(context)
    options = {
        'page-height': '270mm',
        'page-width': '185mm',
    }

    pdf = pdfkit.from_string(html, r'mediafiles/' + file_path, options=options) # new
    
    # print(f'pdf:{pdf}')
    return pdf,file_path


# dont use this
class GenerateInvoice(APIView):

    # permission_classes = []
    # authentication_classes = []

    def post(self,request):

        try:
            if request.user.is_authenticated:

                if not InvoiceDetail.objects.filter(user=request.user).exists():
                    return Response({"success": False, "error":False, "message": "User dont have any Invoice to generate PDF !"})

                invoice = InvoiceDetail.objects.filter(user=request.user).order_by('-created_at')[0]

                if (not invoice.invoice_file == "" or invoice.invoice_file == None):
                    print("")
                    return Response({"success": False, "error":False, "message": "PDF is already generated and saved !", "invoice_pdf_link":invoice.invoice_file.url})

                issue_date = datetime.date.today()
                template_src = 'Invoicetemplate/index.html'


                invoice_obj = InvoiceDetail.objects.last()
                if invoice_obj is not None:
                    invoice_number = invoice_obj.invoice_number + 1
                else:
                    invoice_number = 1

                payment = PaymentHistory.objects.filter(user=request.user).last()
                package_obj = Packages.objects.filter(user=request.user).last()
                print(f'invoice:{invoice}')
                data = {"email":request.user.email,"address":payment.address,"user_mobile_no":invoice_obj.user_mobile_no,"invoice_number":invoice_number,"subtotal":invoice.sub_total,"total":invoice.total,"amount_due":invoice.amount_due,
                        "plan_start_date":invoice.plan_start_date,"plan_end_date":invoice.plan_end_date,"issue_date":issue_date,
                        "package":invoice.package,"invoice_id":invoice_obj.invoice_number,"stripe_id":payment.stripe_customer_id,
                        "date":invoice_obj.created_at,"plan_name":package_obj.name,
                        "plan_id":package_obj.product_id,"quantity":invoice_obj.quantity,
                        "amount_due":invoice_obj.amount_due,"sub_total":invoice_obj.sub_total,
                        "total":invoice_obj.total
                        }

                print(f'data:{data}')

                temp, file_path = render_to_pdf(template_src,data,'invoice.pdf')
                email = EmailMultiAlternatives(
                    'SayHey BOT Subscription Invoice',
                    'Please find the attachment below',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email,'pankajj112223333@gmail.com','panku526154@gmail.com','connect.siddhiraj@gmail.com','pankajfs19if009@gmail.com']

                )
                print(f'temp:{temp}')
                print(f'file_path:{file_path}')
                print(email)
                email.attach_file(f'{settings.BASE_DIR}/media/'+file_path)
                print(f'count:{email.send()}')
                invoice_obj = InvoiceDetail.objects.filter(id=invoice.id).last()
                invoice_obj.invoice_file=file_path
                invoice_obj.invoice_number=invoice_number
                invoice_obj.save()
                
                PaymentHistory.objects.filter(user=request.user).update(invoice_download_link=invoice_obj.invoice_file.url)
                return Response({"True"})
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})

        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


class PackageInfo(APIView):
    def get(self,request):
        try:
            if request.user.is_authenticated:
                data = InvoiceDetail.objects.filter(user=request.user).values('price_id','package')
                return Response({"data":list(data)})
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})





# stripe payment here


def createStripeCustomer(user, payment_method=None):

    try:

        if payment_method is not None:
            customer = stripe.Customer.create(
                email=user.email,
                payment_method=payment_method,
                description=user.first_name,
                name= user.first_name,
                metadata={
                    "user_email":user.email,
                    }
            )

        else:
            customer = stripe.Customer.create(
                email=user.email,
                description=user.first_name,
                name= user.first_name,
                metadata={
                    "user_email":user.email,
                    }
            )

        return True, customer

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while creating stripe customer !"


def updateStripeCustomer(cus_id, args):

    try:
        customer = stripe.Customer.modify(cus_id, **args)
        return True, customer

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while modifying customer !"


def attachPaymentMethodToStripeCustomer(pm_id, cus_id):

    try:
        response = stripe.PaymentMethod.attach(pm_id, customer=cus_id)
        print("\nresponse :: ", response)

        return True, "Payment method attched successfully !"

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while attaching payment method to user !"


def setDefaultStripePaymentMethod(user, payment_method):
    
    try:

        # update customer default payment method
        args = {
            "invoice_settings":{
                'default_payment_method': payment_method
            }
        }
        
        status_1, updated_customer = updateStripeCustomer(cus_id=user.stripe_customer_id, args=args)
        if not status_1:
            return False, updated_customer

        user.stripe_customer_id = updated_customer.id
        user.stripe_customer_response = updated_customer
        user.save()

        return True, "Set default payment method successfully !"

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while setting users default payment method !"


def createStripePaymentMethod(user, type, card_details={}):

    try:
        payment_method = stripe.PaymentMethod.create(
            type=type,
            card=card_details,
            metadata={
                "user_email": user.email,
                       }
        )

        return True, payment_method

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while creating Stripe Payment Method !"


def deleteStripePaymentMethod(pm_id):
    
    try:

        detach_payment_method = stripe.PaymentMethod.detach(pm_id)

        return True, "Stripe Payment Method deleted successfully !"

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while deleting Stripe Payment Method !"


def updateStripePaymentMethod(pm_id, args):
    
    try:

        update_payment_method = stripe.PaymentMethod.modify(pm_id, **args)

        return True, "Stripe Payment Method updated successfully !"

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while updating Stripe Payment Method !"


def generateInvoiceNumber(user, last_invoice_no):

    in_id = int(last_invoice_no.split('-')[-1]) + 1
    new_in_no = f"{user.id}-{in_id}"
    # new_in_no = random.randint(10000, 9999999)

    return str(new_in_no)


def generateInvoiceFile(user, ph_id):

    try:
        # ph => payment history
        ph = PaymentHistory.objects.filter(id=ph_id).first()
        billing_address = ph.payment_method.billing_address
        name = f"{user.first_name} {user.last_name}" if not user.user_type == "company" else user.company_name

        data = {"name": name, "email": user.email, "address": billing_address, "user_mobile_no": user.mobile_number,
                "invoice_number": ph.invoice.invoice_number, "sub_total": ph.invoice.sub_total,"total": ph.invoice.total, 
                "amount_due":0, "payment_type": ph.payment_type, "currency": ph.payment_method.currency,
                "date": ph.invoice.invoice_date, "stripe_id": ph.payment_id, "recurring_period": ph.package.recurring_period,
                "package_id": ph.package.id, "plan_name": ph.package.name, "quantity": ph.invoice.quantity, "amount_paid": ph.amount
            }
        print(f'data:{data}')

        template_src = 'Invoicetemplate/test_invoice.html'

        temp, file_path = render_to_pdf(template_src, data, f'invoice_{ph.invoice.invoice_number}')
        email = EmailMultiAlternatives(
            'SayHey BOT Subscription Invoice',
            'Please find the attachment below',
            settings.DEFAULT_FROM_EMAIL,
            [user.email, 'pankajj112223333@gmail.com', 'connect.siddhiraj@gmail.com']
        )

        print(f'temp:{temp}')
        print(f'file_path:{file_path}')
        print(email)
        email.attach_file(f'{settings.BASE_DIR}/mediafiles/{file_path}')
        print(f'count:{email.send()}')

        return True, file_path

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while generataing a Invoice pdf !"


def retrieveStripeSubscription(cus_id, subs_id=None):

    try:
        subscription = None
        if subs_id:
            subscription = stripe.Subscription.retrieve(subs_id)
        else:
            subscription = stripe.Subscription.list(
                customer=cus_id,
                status='all',
            )

        return subscription

    except Exception as err:
        print("Error :: ", err)
        return False, "Error occured while fetching subscriptions !"


def test(request):

    # logo_url = "http://127.0.0.1:8000/media/app/normal_users/profile_pictures/img5.jpg"
    # logo_url = "http://127.0.0.1:8080/media/app/normal_users/profile_pictures/backend_logo.png"
    # logo_url = "http://127.0.0.1:8080/media/app/normal_users/profile_pictures/WhatsApp_Image_2022-07-29_at_9.57.06_PM.jpeg"
    logo_url = (str(settings.BASE_DIR) + r"\static\images\backend_logo.png")
    # data = {
    #     'logo_url':logo_url,
    # }

    data = {"name":"siddhiraj r kolwankar", "email":"email@email.com", "address":"billing_address", "user_mobile_no":"9876543210",
            "invoice_number":"90-100", "sub_total":100,"total":100,"amount_due":0, 
            "payment_type": "subscription",
            "date": "10-09-2021", "stripe_id": "stripe_txn_DhdjfksdfLKH123", "recurring_period": 6,
            "plan_id":1, "plan_name": "backend Premium Services", "quantity": 1, "amount_paid": "100"
        }

    return render(request, 'Invoicetemplate/test_invoice.html', data)



class PaymentMethod(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @transaction.atomic
    @csrf_exempt
    def get(self, request):
        
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)

                pid = request.data.get('pid', None)
                if pid is not None:
                    # upi => user_payment_info
                    upi = UserPaymentInfo.objects.filter(user=request.user, id=pid).first().values()
                
                else:
                    # upi => user_payment_info
                    upi = UserPaymentInfo.objects.filter(user=request.user).values()
                
                if upi == None or upi == []:
                    return Response({"success": False, "error":False, "message": "Payment Method not Found !"})

                return Response({"success": True, "error":False, "data": upi, "message": "Fetched all payment methods successfully !"})
            
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


    @transaction.atomic
    @csrf_exempt
    def post(self, request):
        
        try:


    
            if request.user.is_authenticated:
                print("User :: ", request.user)
                user = request.user
                data = request.data
                # data._mutable=True

                status_,customer = createStripeCustomer(user)

                CustomUser.objects.filter(email=user.email).update(stripe_customer_id=customer.id,stripe_customer_response=customer)
               
                if not UserPaymentInfo.objects.filter(user=user, card_no=data['card_no']).exists():
                    
                    card_details = {
                        "number": data['card_no'],
                        "exp_month": data['exp_month'],
                        "exp_year": data['exp_year'],
                        "cvc": data['cvv_no'],
                    }
                    
                    status, payment_method = createStripePaymentMethod(user=user, type=data['ptype'], card_details=card_details)
                    if not status:
                        return Response({"success": False, "error":False, "message": payment_method})



                    if UserPaymentInfo.objects.filter(user=user).count() == 0:
                        print("User dont have any payment method added !")
                        # user added his/her first payment method so set this payment method as default payment method
                        # attach this.payment_method to current user
                        status_a, resps_a = attachPaymentMethodToStripeCustomer(pm_id=payment_method.id, cus_id=user.stripe_customer_id)
                        if not status_a:
                            return Response({"success": False, "error":False, "message": resps_a})
                            
                        status, resps = setDefaultStripePaymentMethod(user=user, payment_method=payment_method.id)
                        if not status:
                            return Response({"success": False, "error":False, "message": resps})
                        
                        # data._mutable=True

                        data["is_default"] = True

                    
                    status_1, msg = attachPaymentMethodToStripeCustomer(pm_id=payment_method.id, cus_id=user.stripe_customer_id)
                    print("msg :: ", msg)
                    if not status_1:
                        return Response({"success": False, "error":False, "message": msg})

                    data["user"] = user.id
                    data["stripe_payment_method_id"] = payment_method.id
                    data["stripe_payment_method_response"] = payment_method

                    new_pi = PostUserPaymentInfoSerializer(data=data)
                    if new_pi.is_valid():
                        new_pi.save()
                    else:
                        print("Errors :: ", new_pi.errors)
                        return Response({"success": False, "error":False, "status": "serializer_error", "serializer_error": new_pi.errors, "message": "Error occured while creating User Payment Info due to invalid data !"})

                    c = data['card_no']
                    card_no = f"{c[0:4]} {c[4:8]} {c[8:12]} {c[12:]}"
                    return Response({"success": True, "error":False, "data":new_pi.data,
                                    "message": f"New Payment Method added successfully for card number {card_no} !" })
                    
                else:
                    return Response({"success": False, "error":False, "message": "We found that you have already added this card !"})

            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


    @transaction.atomic
    @csrf_exempt
    def put(self, request):
        
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)
                user = request.user

                pid = request.data.get('pid', None)
                if pid is not None and UserPaymentInfo.objects.filter(id=pid).exists():
                    
                    pm = UserPaymentInfo.objects.filter(user=user, id=pid).first()

                    # args = {
                    #     "card": {"exp_month":12, "exp_year": 2030}
                    # }

                    args = {
                        "billing_details": {
                            "email":"test@email.com", 
                            "name":"test name", 
                            "phone":"9876543210", 
                            "address": {
                                "line1":"test line 1",
                                "line2":"test line 2",
                                "city":"test city",
                                "country":"test country",
                                "state":"test state",
                                "postal_code":"12345"
                            }
                        },
                        "card": {
                            "exp_month":12, 
                            "exp_year": 2030
                        },
                        "metadata": {
                            "user_email": user.email,
                                                }
                    }

                    status, msg = updateStripePaymentMethod(pm.stripe_payment_method_id, args)
                    if not status:
                        print("msg :: ", msg)
                        return Response({"success": False, "error":False, "message": msg})
                    
                    print("msg :: ", msg)

                    return Response({"success": True, "error":False, "message": "Payment method deleted successfully !"})
                
                else:
                    return Response({"success": False, "error":False, "message": "Payment method Not Found !"})
            
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})
    
    
    @transaction.atomic
    @csrf_exempt
    def delete(self, request):
        
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)

                pid = request.data.get('pid', None)
                if pid is not None and UserPaymentInfo.objects.filter(id=pid).exists():
                    
                    pm = UserPaymentInfo.objects.filter(user=request.user, id=pid).first()
                    status, msg = deleteStripePaymentMethod(pm.stripe_payment_method_id)
                    if not status:
                        print("msg :: ", msg)
                        return Response({"success": False, "error":False, "message": msg})
                    
                    print("msg :: ", msg)
                    pm.delete()

                    return Response({"success": True, "error":False, "message": "Payment method deleted successfully !"})
                
                else:
                    return Response({"success": False, "error":False, "message": "Payment method Not Found !"})
            
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


class Payment(APIView):
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    @transaction.atomic
    @csrf_exempt
    def post(self, request):
    
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)
                
                user = request.user
                payment_type = request.data.get('payment_type', None)
                
                if payment_type == None:
                    return Response({"success": False, "error":False, "message": "payment_type is required !", "status":"payment_type_required"})

                if payment_type == "one-time-payment":

                    payment_method_id = request.data.get('payment_method_id', None)
                    package_id = request.data.get('package_id', None)

                    if payment_method_id == None:
                        return Response({"success": False, "error":False, "message": "Please provide 'payment_method_id' and 'amount' !"})
                    
                    payment_method = UserPaymentInfo.objects.filter(id=payment_method_id).first()
                    package = Packages.objects.filter(id=package_id).first()

                    if payment_method == None:
                        return Response({"success": False, "error":False, "message": "Valid Payment method not Found !"})


                    # st, ms = attachPaymentMethodToStripeCustomer(pm_id="pm_1OY7WtSE5WnqzRUfJupzcvNS", cus_id="cus_PMrFj4xpc1a1DA")

                    # print("ms:",ms)
                    payment = stripe.PaymentIntent.create(
                        customer=user.stripe_customer_id, 
                        payment_method="pm_1OY7WtSE5WnqzRUfJupzcvNS",  
                        currency="inr",
                        amount=request.data.get('amount'),
                        confirm=True,
                        # automatic_payment_methods={"enabled": True},
                        automatic_payment_methods={'allow_redirects': "never","enabled":True},
                    )

                    print("payment :: ", payment)

                    # in_obj => invoice object
                    # in_obj = InvoiceDetail.objects.filter(user=user)
                    # if in_obj is not None:
                    #     last_invoice_no = in_obj.order_by('-id')[0].invoice_number
                    # else:
                    #     last_invoice_no = "0-0"

                    # invoice_no = generateInvoiceNumber(user=user, last_invoice_no=last_invoice_no)

                    # # create invoice details object here 
                    # in_d = InvoiceDetail.objects.create(user=user, invoice_number=invoice_no, invoice_date=date.today(), quantity=1, 
                    #                                     sub_total=package.amount, total=package.amount, price_id=package.price_id, user_mobile_no=user.mobile_number)
                    # in_d.save()


                    # # create payment history object here
                    # # new_ph => new payment history
                    # new_ph = PaymentHistory.objects.create(user=user, package=package, invoice=in_d, payment_method=payment_method, payment_type="one-time-payment", currency=payment_method.currency, 
                    #                                         payment_id=payment.id, payment_response=payment, amount=package.amount)
                    # new_ph.save()

                    # # generate invoice here
                    # status_gi, file_path = generateInvoiceFile(user=user, ph_id=new_ph.id)
                    # if status_gi:
                    #     in_d.invoice_file = file_path
                    #     in_d.save()

                    #     new_ph.invoice_download_link = in_d.invoice_file.url
                    #     new_ph.save()

                    return Response({"success": True, "error":False, "payment_details":payment, "message": "Payment success !"})
            
                return Response({"success": False, "error":False, "message": "Payment type required !"})

            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


class Subscription(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


    @transaction.atomic
    @csrf_exempt
    def get(self, request):
        
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)

                # us_id => user subscription id
                us_id = request.data.get('us_id', None)

                by_status = request.data.get('by_status', None)
                
                if by_status == "all":
                    s_status = {}
                elif by_status == "canceled":
                    s_status = {"status":"canceled"}
                elif by_status == "force_stopped":
                    s_status = {"status":"force_stopped"}
                else:
                    s_status = {"status":"active"}

                if us_id is not None:

                    subscription_obj = UserSubscription.objects.filter(user=request.user, id=us_id, **s_status).first()
                    if subscription_obj is not None:
                        subscription = UserSubscriptionSerializer(subscription_obj).data
                        
                        if subscription['package'] is not None:
                            package = Packages.objects.filter(id=subscription['package']).first()
                            subscription['package'] = PackageSerializer(package).data

                    else:
                        return Response({"success": False, "error":False, "message": f"Subscription not found with id : {us_id} !"})

                else:
                    subscription_obj = UserSubscription.objects.filter(user=request.user, **s_status)
                    if len(subscription_obj) > 0:
                        subscription = UserSubscriptionSerializer(subscription_obj.order_by('-id')[0]).data

                        if subscription['package'] is not None:
                            package = Packages.objects.filter(id=subscription['package']).first()
                            subscription['package'] = PackageSerializer(package).data
                    
                    else:
                        return Response({"success": False, "error":False, "message": f"Subscription not found !"})
                
                if subscription == None or subscription == []:
                    return Response({"success": True, "error":False, "message": "No any active Subscription Found !"})

                return Response({"success": True, "error":False, "data": subscription, "message": "Fetched all Subscriptions successfully !"})
            
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


    @transaction.atomic
    @csrf_exempt
    def post(self, request):
        
        try:

            if request.user.is_authenticated:

                print("User :: ", request.user)
                user = request.user

                new_pm = request.data.get('new_pm', None)
                package_id = request.data.get('package_id', None)
                pm_id = request.data.get('pm_id', None)

                if package_id == None:
                    return Response({"success": False, "error":False, "message": "Please provide 'package_id' and 'subs_plan' !"})

                # if user is adding a new payment method at the time of subscription
                if new_pm is not None and (new_pm == "true" or new_pm == True):
                    card_details = request.data.get('card_details', None)
                    ptype = request.data.get('ptype', None)

                    sdata = {
                        "card_no": card_details['number'],
                        "exp_month": card_details['exp_month'],
                        "exp_year": card_details['exp_year'],
                        "cvv_no": card_details['cvc'],
                        "currency": request.data.get('currency', None),
                        "billing_address": request.data.get('billing_address', None),
                        "ptype": ptype
                    }

                    if (card_details is not None and card_details != {}) and (ptype is not None and ptype == "card"):

                        if not UserPaymentInfo.objects.filter(user=user, card_no=card_details['number']).exists():
                            
                            status, payment_method = createStripePaymentMethod(user=user, type=ptype, card_details=card_details)
                            if not status:
                                return Response({"success": False, "error":False, "message": payment_method})

                            status_a, resps_a = attachPaymentMethodToStripeCustomer(pm_id=payment_method.id, cus_id=user.stripe_customer_id)
                            if not status_a:
                                return Response({"success": False, "error":False, "message": resps_a})
                            
                            status, resps = setDefaultStripePaymentMethod(user=user, payment_method=payment_method.id)
                            if not status:
                                return Response({"success": False, "error":False, "message": resps})
                            
                            sdata["is_default"] = True
                            sdata["user"] = user.id
                            sdata["stripe_payment_method_id"] = payment_method.id
                            sdata["stripe_payment_method_response"] = payment_method
                                
                            # data._mutable=False

                            new_pi = PostUserPaymentInfoSerializer(data=sdata)
                            if new_pi.is_valid():
                                new_pi.save()
                                new_pi = new_pi.data
                                # print("new_pi", new_pi)
                                # make all other payment method default = False
                                UserPaymentInfo.objects.filter(user=user).exclude(id=new_pi['id']).update(is_default=False)
                            else:
                                print("Errors :: ", new_pi.errors)
                                return Response({"success": False, "error":False, "status": "serializer_error", "serializer_error": new_pi.errors, "message": "Error occured while creating User Payment Info due to invalid data !"})

                        else:
                            return Response({"success": False, "error":False, "message": "We found that you have already added this card !"})

                package = Packages.objects.filter(id=package_id).first()
                
                subs_args = {
                    "items":[{'price': package.price_id}]
                }

                if pm_id is not None:
                    # pm => payment method
                    pm = UserPaymentInfo.objects.filter(id=pm_id).first()
                    print(f"currency: {pm.currency}")
                    subs_args["default_payment_method"] = pm.stripe_payment_method_id
                    subs_args["currency"] = package.currency
                else:
                    pm = UserPaymentInfo.objects.filter(user=user, is_default=True).first()

                # make subscription here
                subscription = stripe.Subscription.create(
                    customer=user.stripe_customer_id,
                    **subs_args
                )

                # new_subs => new subscription
                new_subs = UserSubscription.objects.create(user=user, package=package, subscription_plan=package.name, stripe_customer_id=subscription.customer,
                                                            stripe_subscription_id=subscription.id, stripe_subscription_response=subscription)
                new_subs.save()

                # in_obj => invoice object
                in_obj = InvoiceDetail.objects.filter(user=user)
                # print("in_obj :: ", in_obj)
                if len(in_obj) > 0:
                    last_invoice_no = in_obj.order_by('-id')[0].invoice_number
                else:
                    last_invoice_no = "0-0"

                invoice_no = generateInvoiceNumber(user=user, last_invoice_no=last_invoice_no)

                # create invoice details object here 
                in_d = InvoiceDetail.objects.create(user=user, invoice_number=invoice_no, invoice_date=date.today(), quantity=1, 
                                                    sub_total=package.amount, total=package.amount, price_id=package.price_id, user_mobile_no=user.mobile_number)
                in_d.save()

                # create payment history object here
                # new_ph => new payment history
                new_ph = PaymentHistory.objects.create(user=user, package=package, invoice=in_d, payment_method=pm, payment_type="subscription", currency=pm.currency, 
                                                        payment_id=subscription.id, payment_response=subscription, amount=package.amount)
                new_ph.save()

                # generate invoice here
                status_gi, file_path = generateInvoiceFile(user=user, ph_id=new_ph.id)
                if status_gi:
                    in_d.invoice_file = file_path
                    in_d.save()

                    new_ph.invoice_download_link = in_d.invoice_file.url
                    new_ph.save()

                data = UserSubscriptionSerializer(new_subs).data
                
                if data['package'] is not None:
                    package = Packages.objects.filter(id=data['package']).first()
                    data['package'] = PackageSerializer(package).data

                return Response({"success": True, "error":False, "message":"Subscription added successfully !", "data": data})
                # return Response({"success": True, "error":False, "message":"Subscription added successfully !", "data": data, "subscription_test":subscription})

            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


    @transaction.atomic
    @csrf_exempt
    def delete(self, request):
        
        try:

            if request.user.is_authenticated:
                print("User :: ", request.user)

                # us_id => user subscription id
                us_id = request.data.get('us_id', None)
                if us_id is not None:
                    
                    if UserSubscription.objects.filter(id=us_id, status="active").exists():

                        subs = UserSubscription.objects.filter(id=us_id).first().stripe_subscription_id
                        # delete stripe subscription
                        deleted_subs = stripe.Subscription.delete(subs)
                        if deleted_subs['status'] == "canceled":
                            UserSubscription.objects.filter(user=request.user, id=us_id).update(status="canceled", stripe_subscription_response=deleted_subs)

                            return Response({"success": True, "error":False, "message": "Subscription deleted successfully !"})
                    else:
                        return Response({"success": False, "error":False, "message": "Subscription Not Found !"})
                else:
                    return Response({"success": False, "error":False, "message": "Subscription ID required !", "status": "subscription_id_required"})

            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


class SetDefaultPaymentMethod(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @transaction.atomic
    @csrf_exempt
    def post(self, request):
        
        try:

            if request.user.is_authenticated:
                pm_id = request.data.get('pid', None)
                user = request.user

                if pm_id is not None and UserPaymentInfo.objects.filter(id=pm_id).exists():
                    payment_method = UserPaymentInfo.objects.filter(id=pm_id).first()

                    # setting default payment method of stripe customer
                    status, resps = setDefaultStripePaymentMethod(user=user, payment_method=payment_method.stripe_payment_method_id)
                    if not status:
                        return Response({"success": False, "error":False, "message": resps})

                    UserPaymentInfo.objects.filter(user=user).update(is_default=False)
                    payment_method.is_default = True
                    payment_method.save()
                    c = payment_method.card_no
                    card_no = f"{c[0:4]} {c[4:8]} {c[8:12]} {c[12:]}"
                    return Response({"success": True, "error":False, "message": f"Payment Method set to default for card number :: '{card_no}' !"})
            
                return Response({"success": False, "error":False, "message": "Please provide correct User Payment Method id !"})
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})


        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


##CRUD for Payment history 

class PaymentHistoryCRUD(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            id = request.query_params.get('id')
            if id is not None:
                if id != "list":
                    if PaymentHistory.objects.filter(id=id).exists():
                        queryset = PaymentHistory.objects.filter(id=id)
                        data = PaymentHistorySerializer(queryset, many=True)
                        return Response({"success":True, "message":"specified PaymentHistory fetched!", "data":data.data})
                    else:
                        return Response({"success":False, "message":"specified PaymentHistory data does not found!"})
                
                else:
                    queryset = PaymentHistory.objects.filter()
                    data = PaymentHistorySerializer(queryset, many=True)
                    return Response({"success":True, "message":"all PaymentHistory fetched!", "data":data.data})

            else:
                return Response({"success":False, "message":"provide id no or pass 'list' "})
        
        except Exception as err:
            return Response({"success":False, "message":f"Error occured! -- Found Following Error :: {err}"})

    def post(self, request):
        try:
            if request.data is not None:
                print("create duplicate record :: ", request.data.get('duplicate'))
                if not PaymentHistory.objects.filter(id=(request.data.get('id'))).exists() or (request.data.get('duplicate')) :
                    new_PaymentHistory = PaymentHistorySerializer(data=request.data)
                    if new_PaymentHistory.is_valid():
                        new_PaymentHistory.save()
                        return Response({"success":True, "message":"new PaymentHistory created!", "data":new_PaymentHistory.data})
                    else:
                        return Response({"success":False, "message":"new PaymentHistory not created! -- wrong data passed."})
                else:
                    return Response({"success":False, "message":"this record already exists."})
            else:
                return Response({"success":False, "message":"None data passed! -- pass data or valid data"})
        
        except Exception as err:
            return Response({"success":False, "message":f"Error occured! -- Found Following Error :: {err}"})


    def put(self, request):
        try:
            id = request.query_params.get('id')
            if id is not None:
                if id != "list":
                    if PaymentHistory.objects.filter(id=id).exists():
                        PaymentHistory_update = PaymentHistory.objects.filter(id=id)
                        for std in PaymentHistory_update:
                            new_PaymentHistory = PaymentHistorySerializer(instance=std, data=request.data)
                            print("new_PaymentHistory :: ", new_PaymentHistory)
                            if new_PaymentHistory.is_valid():
                                new_PaymentHistory.save()
                            else:
                                print("invalid data!")
                                return Response({"success":False, "message":"PaymentHistory not updated! -- wrong data passed."})
                        if request.data.get('id') is not None:
                            id = request.data.get('id')
                        all_updated_std = PaymentHistory.objects.filter(id=id)
                        data = PaymentHistorySerializer(all_updated_std, many=True)
                        return Response({"success":True, "message":"PaymentHistory updated!", "data":data.data})
                        # else:
                        #     return Response({"success":False, "message":"PaymentHistory not updated! -- wrong data passed."})
                    else:
                        return Response({"success":False, "message":"specified PaymentHistory data does not found!"})
                
                else:
                    all_records = PaymentHistory.objects.filter()
                    for record in all_records:
                        new_PaymentHistory = PaymentHistorySerializer(instance=record, data=request.data)
                        if new_PaymentHistory.is_valid():
                            new_PaymentHistory.save()
                        else:
                            print("Invalid data")
                    
                    data = PaymentHistory.objects.filter().values()
                    return Response({"success":True, "message":"all PaymentHistory updated!", "data":data})
                    # else:
                    #     return Response({"success":False, "message":"all PaymentHistory not updated! -- wrong data passed."})
            else:
                return Response({"success":False, "message":"provide id no or pass 'list' "})

        except Exception as err:
            return Response({"success":False, "message":f"Error occured! -- Found Following Error :: {err}"})

    def delete(self, request):
        try:
            id = request.query_params.get('id')
            if id is not None:
                if PaymentHistory.objects.filter(id=id).exists():
                    PaymentHistory.objects.filter(id=id).delete()
                    return Response({"success":True, "message":"specified PaymentHistory deleted!"})
                else:
                    return Response({"success":False, "message":"specified PaymentHistory data does not found!"})
            else:
                return Response({"success":False, "message":"provide id no"})

        except Exception as err:
            return Response({"success":False, "message":f"Error occured! -- Found Following Error :: {err}"})



class PaymentHistoryData(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self,request):
        try:
            if request.user.is_authenticated:
                data = PaymentHistory.objects.filter(user=request.user).values('package','invoice_download_link','amount','created_at')
                return Response({"success":True,"data":list(data)})
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"})

        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()})


class PackagesView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self,request):
        try:
            if request.user.is_authenticated:
                free_package = Packages.objects.filter(name="Free",price_id="0").first()
                monthly_pro_package = Packages.objects.filter(name="Pro",recurring_period="1").first()
                yearly_pro_package = Packages.objects.filter(name="Pro",recurring_period="12").first()
                monthly_expert_package = Packages.objects.filter(name="Expert",recurring_period="1").first()
                yearly_expert_package = Packages.objects.filter(name="Expert",recurring_period="12").first()

                free_package_data = PackageSerializer(free_package).data
                monthly_pro_package_data = PackageSerializer(monthly_pro_package).data
                yearly_pro_package_data = PackageSerializer(yearly_pro_package).data
                monthly_expert_package_data = PackageSerializer(monthly_expert_package).data
                yearly_expert_package_data = PackageSerializer(yearly_expert_package).data

                return Response({"success":True,"packages":{"free":free_package_data,"monthly_pro":monthly_pro_package_data,"yearly_pro":yearly_pro_package_data,"monthly_expert":monthly_expert_package_data,"yearly_expert":yearly_expert_package_data}})
            else:
                return Response({"success": False, "error":False, "message": "No logged in user found. Login required !"},status=status.HTTP_401_UNAUTHORIZED)

        except Exception as err:
            print("Error occured! :: ", err)
            return Response({"success":False, "error":True, "message": f"Error occured! :: Error was -- {err}", "traceback_info": traceback.format_exc()},status=status.HTTP_503_SERVICE_UNAVAILABLE)


