from datetime import timedelta, datetime
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import auth
from django.db import transaction
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *
import random
import uuid
from django.http import JsonResponse

from rest_framework.decorators import api_view
from django.db.models import Avg, F


# global function here


def sendOTPEmail(email, name, action):

    check_otp, token = createUserVerificationToken(email=email, action=action)
    print(f"\nOTP :: {check_otp} --- token :: {token}")
    domain = "http://127.0.0.1:8000"
    url = f"{domain}api/v1/app/link/verify/{token}"

    subject = f"Welcome to Interview.AI {name} !"
    msg = f"OTP :: {check_otp}"
    html_message = render_to_string('mail_template/signup.html', {"check_otp": check_otp, "check_url": url})

    res = send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [email, "siddhirajk77gmail.com"], html_message=html_message, fail_silently=False)
    print("res :: ", res)

    if res == 1:
        return True
    else:
        return False




def createUserVerificationToken(email, action):

    UserVerification.objects.filter(email=email, action=action).delete()

    check_otp = random.randint(10000, 99999)
    token = f"{uuid.uuid4()}{uuid.uuid4()}"

    if UserVerification.objects.filter(token=token).exists():
        token = f"{token}{random.randint(100000000, 9999999999)}"

    new_token = UserVerification.objects.create(email=email, otp=check_otp, token=token, action=action, token_expire_on=(
                                                datetime.now() + timedelta(days=1)), otp_expire_on=(datetime.now() + timedelta(minutes=10)))
    new_token.save()

    return check_otp, token




# Create your views here.


def test(request):
    return render(request, 'temp_video.html')


def verifyLink(request, token):
    print("\nToken :: ", token)

    return HttpResponse("Verified !")




class Register(APIView):

    permission_classes = []
    authentication_classes = []

    @transaction.atomic
    def post(self, request):

        rd = request.data
        print("rd :: ", rd)

        if CustomUser.objects.filter(email=rd['email']).exists():
            return Response({"success": False, "message": f"User with email '{rd['email']}' already exists !"})

        if not sendOTPEmail(rd['email'], rd['fname'], "signup"):
            return Response({"success":False, "message": "Email not sent !"})

        new_user = CustomUser.objects.create_user(email=rd['email'], username=rd['email'], password=rd['password'],
                                                  first_name=rd['fname'], last_name=rd['lname'])

        data = {"email": rd['email'], "name": rd['fname'], "action": "signup"}

        return Response({"success": True, "message": "Successful !", "data": data})


class Login(APIView):

    permission_classes = []
    authentication_classes = []

    @transaction.atomic
    def post(self, request):

        rd = request.data
        print("rd :: ", rd)

        user = auth.authenticate(email=rd['email'], password=rd['password'])
        print("user:",user)
        if user is not None:

            # if not user.is_verified:
            #     return Response({"success": False, "message": "Email is not verified. Please verify Email and try Again !"})

            token = RefreshToken.for_user(user)
            data = GetCustomUserSerializer(user).data

            return Response({"success": True, "message": "User login successfully !", "data": data,
                            "authToken": {
                                'type': 'Bearer',
                                'access': str(token.access_token),
                                'refresh': str(token),
                            }})
        else:
            return Response({"success": False, "message": "Oppps! Creadentials does not matched!"})


class VerifyUser(APIView):

    @transaction.atomic
    def post(self, request, vmode):

        rd = request.data
        print("rd :: ", rd)

        UserVerification.objects.filter(token_expire_on__lte=datetime.now()).delete()
        token_obj = None

        if vmode == "otp":
            token_obj = UserVerification.objects.filter(email=rd['email'], otp=rd['otp'], action=rd['action'], otp_expire_on__gte=datetime.now()).first()
        elif vmode == "token":
            token_obj = UserVerification.objects.filter(token=rd['token'], token_expire_on__gte=datetime.now()).first()
            rd['email'] = token_obj.email
            rd['action'] = token_obj.action

        if token_obj != None and rd['action'] == "signup":

            token_obj.delete()
            user = CustomUser.objects.filter(email=rd['email']).first()
            user.is_verified=True
            user.email_verified_at=datetime.now()
            user.save()

            token = RefreshToken.for_user(user)
            data = GetCustomUserSerializer(user).data

            return Response({"success": True, "message": "User Registration successful !", "data": data,
                            "authToken": {
                                'type': 'Bearer',
                                'access': str(token.access_token),
                                'refresh': str(token),
                            }})

        else:
            return Response({"success": False, "message": "OTP/Token does not matched!"})

        # return Response({"success": False, "message": "Something went wrong !"})


class ResendOTP(APIView):

    permission_classes = []
    authentication_classes = []

    @transaction.atomic
    def post(self, request):

        rd = request.data
        print("rd :: ", rd)

        if not sendOTPEmail(rd['email'], rd['fname'], rd['action']):
            return Response({"success":False, "message": "Email not sent !"})
        else:
            return Response({"success":True, "message": "Email sent successfully !"})




@api_view(['GET'])
def hello_world(request):
    return JsonResponse({"message": "Hello World!"})




import requests    
import json
from bs4 import BeautifulSoup
from django.http import JsonResponse
from rest_framework.decorators import api_view
@api_view(['GET'])
def scrap_from_indian_oil(request):

    ip = request.META.get('REMOTE_ADDR')
    print("ip:", request.META)
    location = request.GET.get('location')
    stores_data = []
    url = "https://locator.iocl.com/?search={}".format(location)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # The request was successful
        html_content = response.content.decode("utf-8")
        soup = BeautifulSoup(html_content, 'html.parser')
        for store_info_box in soup.select('.store-info-box'):
            business_name = store_info_box.select_one('.outlet-name a').text.strip()
            distance = store_info_box.select_one('.outlet-distance .info-text').text.strip()
            alternate_name = store_info_box.select_one('.outlet-actions .btn-website')['data-track-event-business-alternate-name']
            address_lines = store_info_box.select('.outlet-address .info-text span')
            address = ' '.join(line.text.strip() for line in address_lines)
            phone_number = store_info_box.select_one('.outlet-phone a').text.strip()
            opening_hours = store_info_box.select_one('.outlet-timings .info-text').text.strip()
            map_link = store_info_box.select_one('.outlet-actions .btn-map')['href']
            details_link = store_info_box.select_one('.outlet-actions .btn-website')['href']

            # Extract latitude and longitude values from hidden input fields
            latitude = store_info_box.select_one('.outlet-latitude')['value']
            longitude = store_info_box.select_one('.outlet-longitude')['value']

            # Create a dictionary for the current store-info-box
            store_data = {
                "business_name": business_name,
                "distance": distance,
                "alternate_name": alternate_name,
                "address": address,
                "phone_number": phone_number,
                "opening_hours": opening_hours,
                "map_link": map_link,
                "details_link": details_link,
                "latitude": latitude,
                "longitude": longitude,
            }

            # Add the dictionary to the list
            stores_data.append(store_data)

        # Convert the list of dictionaries to a JSON array
        json_array = json.dumps(stores_data, indent=2)

        # Convert the JSON string to a JSON object
        json_object = json.loads(json_array)

        # Print the JSON object
        print(json_object)

        return JsonResponse({"data": json_object}, content_type='application/json')

    else:
        # The request failed
        print(f"Failed to fetch data. Status code: {response.status_code}")
        print("Response content:", response.text)

        return JsonResponse({"error": "Failed to fetch data"}, status=500)
from bs4 import BeautifulSoup

import json
@api_view(['GET'])
def puc_data(request):
    location = request.data.get('location')
    url = "https://www.indiacom.com/yellow-pages/p-u-c--center/{}".format(location)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # The request was successful
        html_content = response.content.decode("utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    result_info_list = []

    for resultbox_info in soup.find_all('div', class_='mx-2'):
        name = resultbox_info.find('h2').text.strip()
        address = resultbox_info.find('address').text.strip()
        # phone_link = resultbox_info.find('a', class_='btn m-1')['href']
        # Extracting phone number from the link
        # phone_number = phone_link.split('/')[-1].replace('.html', '')

        result_info_list.append({
            'name': name,
            'address': address,
            # 'phone_number': phone_number,
        })

    print("result_info_list:",result_info_list)

    return JsonResponse({"data": result_info_list})

@api_view(['POST'])
def register_garage(request):
    basic = request.data['basic']
    garage  = request.data['garage']
    subscriptionEnabled = request.data['garage'].get('subscription_enabled',False)
    user = CustomUser.objects.create(email=basic['email'],
                              first_name=basic['first_name'],
                              last_name=basic['last_name'],
                              mobile_number=basic['mobile_number'],
                              gender = basic['gender'])
    Garage.objects.create(user=user,name=garage['name'],
                          address=garage['address'],
                          subscriptionEnabled=subscriptionEnabled)
    return JsonResponse({"message":"Garage Created Successfully"})

    


@api_view(['GET'])
def get_garage(request):
    place = request.GET.get('place')

    queryset = Garage.objects.annotate(avg_rating=Avg('rating__rating')).order_by('-subscriptionEnabled', '-avg_rating')

    if place:
        # If 'place' parameter is provided, filter based on address containing the specified place
        queryset = queryset.filter(address__icontains=place)

    data = GarageSerializer(queryset, many=True).data
    return JsonResponse({'data': data})


@api_view(['POST'])
def rate_garage(request):
    garage_id = request.data.get('garage_id')
    rating = request.data.get('rating')
    garage = Garage.objects.get(id=garage_id)
    Rating.objects.create(garage=garage,rating=rating)
    return JsonResponse({'message': "Rating Added!"})

