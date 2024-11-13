from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
# from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Max
from django.core.mail import send_mail

from .forms import UserRegistrationForm
from .models import Driver, Request, ShareRide #, User 

@login_required
def homepage(request):
    return render(request, "ride_sharing/homepage.html")
    #return HttpResponse("Welcome to the ride sharing service! Click on the menu bar to continue")

def user_register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Account Created for {username}. You can now log in")
            return redirect("login")
    else:   
        form = UserRegistrationForm()
    return render(request, "ride_sharing/user_register.html", {"form": form})

# @login_required
# def send_email(request):
#     send_mail(
#     "Subject here",
#     "Here is the message.",
#     "yhece568@yahoo.com",
#     ["aybucydu9@gmail.com"],
#     fail_silently=False,)
#     return HttpResponse("successfully sent email")
#    return render(request, "ride_sharing/place_request.html")

@login_required
def place_request(request):
    return render(request, "ride_sharing/place_request.html")

@login_required
def my_requests(request):
    if request.method == "POST":
        # sharer join a shared ride
        if request.POST.get("request_id_sharer_join"):
            try:
                existing_shareride = ShareRide.objects.get(sharer=request.user, booking=Request.objects.get(pk = int(request.POST["request_id_sharer_join"])))
                messages.error(request, f"You have already shared this ride before and can not join again. If you want to update your share request, please use the edit function!")
            except (KeyError, ShareRide.DoesNotExist):
                new_shareride = ShareRide(
                            sharer=request.user,
                            booking=Request.objects.get(pk = int(request.POST["request_id_sharer_join"])), 
                            num_sharer = request.POST["num_sharer"]
                            )
                new_shareride.save()
                share_destination = Request.objects.get(pk = int(request.POST["request_id_sharer_join"])).destination
                messages.success(request, f"Your Have successfully joined the shared ride to {share_destination}")

        # sharer cancle a shared ride    
        elif request.POST.get("cancel_ride_sharer"):
            shareride_to_delete = ShareRide.objects.get(booking=request.POST["cancel_ride_sharer"], sharer=request.user)
            shareride_to_delete.delete()
        
        # owner cancled a ride
        elif request.POST.get("cancel_ride"):
            request_to_delete = Request.objects.get(pk=request.POST["cancel_ride"])
            request_to_delete.delete()
        
        # place a new request
        else:
            # check input data validity
            if int(request.POST["num_passengers"]) < 1:
                messages.error(request, "Number of passenger can not be less than 1. Please correct your request info and place request again.")
                return render(request, "ride_sharing/place_request.html", {"current_data" : request.POST})
            elif int(request.POST["num_passengers"]) > 6:
                messages.error(request, "Number of passenger can not be more than 6. Please correct your request info and place request again.")
                return render(request, "ride_sharing/place_request.html", {"current_data" : request.POST})
            
            new_request = Request(owner=request.user, 
                            destination=request.POST["destination"], 
                            expected_arrival_time = request.POST["expected_arrival_time"],
                            num_passengers = request.POST["num_passengers"],
                            vehicle_type = request.POST["vehicle_type"],
                            special_request = request.POST["special_request"],
                            can_share = True if request.POST.get("can_share") == "on" else False,
                            is_open = True,
                            is_complete = False)
            new_request.save()
    
    # general - display request
    my_request_list = Request.objects.filter(owner=request.user) | Request.objects.filter(shareride__sharer=request.user)
    my_request_list = my_request_list.values("id", 
                                                "owner",
                                                "shareride__booking", 
                                                "destination", 
                                                "expected_arrival_time", 
                                                "num_passengers", 
                                                "can_share", 
                                                "is_open", 
                                                "is_complete").annotate(total_sharer = Sum("shareride__num_sharer"),
                                                                        total_pax = Sum("shareride__num_sharer") + Max("num_passengers"))
    my_request_list = my_request_list.exclude(is_complete=True).order_by("-expected_arrival_time")
    context = {"my_request_list": my_request_list, "cur_user": request.user}
    return render(request, "ride_sharing/my_requests.html", context)

@login_required
def view_request_detail(request):
    if request.method == "POST":
        # sharer edit ride details
        if request.POST.get("confirm_sharer"):
            if int(request.POST["num_sharer"]) < 1:
                messages.error(request, "Number of sharer can not be less than 1. Please correct your request info and place request again.")
                shareride_info = ShareRide.objects.get(booking=request.POST["confirm_sharer"], sharer=request.user) 
                return render(request, "ride_sharing/edit_request_detail_sharer.html", 
                                        {"shareride_info": shareride_info,"current_data" : request.POST})
            elif int(request.POST["num_sharer"]) > 5:
                messages.error(request, "Number of sharer can not be more than 5. Please correct your request info and place request again.")
                shareride_info = ShareRide.objects.get(booking=request.POST["confirm_sharer"], sharer=request.user) 
                return render(request, "ride_sharing/edit_request_detail_sharer.html", {"shareride_info": shareride_info,"current_data" : request.POST})

            shareride_to_update = ShareRide.objects.get(booking=request.POST["confirm_sharer"], sharer=request.user)
            shareride_to_update.num_sharer = request.POST["num_sharer"]
            shareride_to_update.save()
            selected_request = Request.objects.get(pk=request.POST["confirm_sharer"])
        # owner edit ride details
        elif request.POST.get("confirm"):
            if int(request.POST["num_passengers"]) < 1:
                messages.error(request, "Number of passengers can not be less than 1. Please correct your request info and place request again.")
                request_info = Request.objects.get(pk=request.POST["confirm"])
                formatted_time = request.POST["expected_arrival_time"]
                return render(request, "ride_sharing/edit_request_detail_owner.html", 
                    {"request_info": request_info, "formatted_time": formatted_time, "current_data" : request.POST})
                
            elif int(request.POST["num_passengers"]) > 6:
                messages.error(request, "Number of passengers can not be more than 6. Please correct your request info and place request again.")
                request_info = Request.objects.get(pk=request.POST["confirm"])
                formatted_time = request.POST["expected_arrival_time"]
                return render(request, "ride_sharing/edit_request_detail_owner.html", 
                    {"request_info": request_info, "formatted_time": formatted_time, "current_data" : request.POST})

            request_to_update = Request.objects.get(pk=request.POST["confirm"])
            request_to_update.destination = request.POST["destination"]
            request_to_update.expected_arrival_time = request.POST["expected_arrival_time"]
            request_to_update.num_passengers = request.POST["num_passengers"]
            request_to_update.can_share = True if request.POST.get("can_share") == "on" else False
            request_to_update.vehicle_type = request.POST["vehicle_type"]
            request_to_update.special_request = request.POST["special_request"]
            request_to_update.save()
            selected_request = Request.objects.get(pk=request.POST["confirm"])
        else:
            selected_request = Request.objects.get(pk=request.POST["request_id"])
        return render(request, "ride_sharing/view_request_detail.html", {"request": selected_request, "cur_user": request.user})

@login_required
def edit_request_detail_owner(request):
    if request.method == "POST":
        request_info = Request.objects.get(pk=request.POST["request_id"])
        formatted_time = request_info.expected_arrival_time.astimezone().strftime('%Y-%m-%dT%H:%M')
        return render(request, "ride_sharing/edit_request_detail_owner.html", 
                    {"request_info": request_info, "formatted_time": formatted_time})

@login_required
def edit_request_detail_sharer(request):
    if request.method == "POST":
        shareride_info = ShareRide.objects.get(booking=request.POST["request_id"], sharer=request.user) 
        return render(request, "ride_sharing/edit_request_detail_sharer.html", 
                                {"shareride_info": shareride_info})

@login_required
def driver_profile(request):
    # confirm edit driver profile
    if request.method == "POST" and request.POST.get("confirm"):
        # check input invalidity
        if int(request.POST["max_passenger_num"]) < 1:
                messages.error(request, "Maximum Number of Passenger can not be less than 1. Please correct your input and save again.")
                driver_info = Driver.objects.get(user=request.user)
                return render(request, "ride_sharing/edit_driver_profile.html", {"driver_info": driver_info, "current_data" : request.POST})
                
        elif int(request.POST["max_passenger_num"]) > 6:
            messages.error(request, "Maximum Number of Passenger can not be more than 6. Please correct your input and save again.")
            driver_info = Driver.objects.get(user=request.user)
            return render(request, "ride_sharing/edit_driver_profile.html", {"driver_info": driver_info, "current_data" : request.POST})

        driver_to_update = Driver.objects.get(user=request.user)
        driver_to_update.name = request.POST["your_name"]
        driver_to_update.vehicle_type = request.POST["vehicle_type"]
        driver_to_update.license_plate_num = request.POST["license_plate_num"]
        driver_to_update.max_passenger_num = request.POST["max_passenger_num"]
        driver_to_update.special_vehicle_info = request.POST["special_vehicle_info"]
        driver_to_update.save()
    driver_info = Driver.objects.get(user=request.user)
    return render(request, "ride_sharing/driver_profile.html", {"driver_info": driver_info})

@login_required
def edit_driver_profile(request):
    if request.method == "POST":
        driver_info = Driver.objects.get(user=request.user)
        return render(request, "ride_sharing/edit_driver_profile.html", {"driver_info": driver_info})

@login_required
def driver_view_confirmed_requests(request):
    # if we go to this page from the claim request page, we need to process the data first
    if request.method == "POST":
        if request.POST.get("complete_request_id"):
            finished_request = Request.objects.get(pk=request.POST["complete_request_id"])
            finished_request.is_complete = True
            finished_request.save()
        else:
            selected_request = Request.objects.get(pk=request.POST["request_id"])
            selected_request.driver = Driver.objects.get(user=request.user)
            selected_request.is_open = False
            selected_request.save()

            # send email to owner and sharer that the request has been confirmed
            service = gmail_authenticate()
            email_content = "<h2>You're in good hands cause our amazing driver " + request.user.username + " will make sure you get to " + selected_request.destination + " safely!</h2><h2>Enjoy your ride!</h2>"
            # send to owner
            send_message(service, 
                        "yhece568@gmail.com", 
                        selected_request.owner.email, 
                        "Your ride to " + selected_request.destination + " has been confirmed!", 
                        email_content)
            # send to sharer
            share_list = ShareRide.objects.filter(booking=request.POST["request_id"])
            for share in share_list:
                send_message(service, 
                        "yhece568@gmail.com", 
                        share.sharer.email, 
                        "Your shared ride to " + selected_request.destination + " has been confirmed!", 
                        email_content)

    my_request_list = Request.objects.filter(driver=Driver.objects.get(user=request.user), is_complete=False).order_by("-expected_arrival_time")
    my_request_list = my_request_list.values("id", 
                                                "owner",
                                                "shareride__booking", 
                                                "destination", 
                                                "expected_arrival_time", 
                                                "num_passengers", 
                                                "can_share", 
                                                "is_open", 
                                                "is_complete").annotate(total_sharer = Sum("shareride__num_sharer"),
                                                                        total_pax = Sum("shareride__num_sharer") + Max("num_passengers"))
    context = {"my_request_list": my_request_list}
    return render(request, "ride_sharing/driver_view_confirmed_requests.html", context)

@login_required
def driver_registration(request):
    return render(request, "ride_sharing/driver_registration.html")

@login_required
def driver_registration_result(request):
    #this_user = get_object_or_404(User, pk=user_id)
    # try:
    #     selected_user = user.request_set.get(pk=request.POST["choice"])
    # except (KeyError, Choice.DoesNotExist):
    #     # Redisplay the question voting form.
    #     return render(
    #         request,
    #         "polls/detail.html",
    #         {
    #             "question": question,
    #             "error_message": "You didn't select a choice.",
    #         },
    #     )
    # else:
    try:
        driver_info = Driver.objects.get(user=request.user)
        messages.error(request, f"You already have a Driver Profile. If you want to update your profile, you can do it at this page!")
    except (KeyError, Driver.DoesNotExist):
        new_driver = Driver(user=request.user, 
                            name=request.POST["your_name"], 
                            vehicle_type = request.POST["vehicle_type"],
                            license_plate_num = request.POST["license_plate_num"],
                            max_passenger_num = request.POST["max_passenger_num"],
                            special_vehicle_info = request.POST["special_vehicle_info"])
        new_driver.save()
        driver_info = Driver.objects.get(user=request.user)
        messages.success(request, f"Your Driver Profile has been created.")
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return render(request, "ride_sharing/driver_profile.html", {"driver_info": driver_info})
    # return redirect("ride_sharing:driver_profile", {"driver_info": driver_info})

@login_required
def driver_search_for_open_request(request):
    # filter for 
    # 1. open status 
    # 2. vehicle type 
    # 3. special info 
    # 4. request not made by the driver (it will be very confusing for driver to see and try to book their own booking)
    # 5. vehicle capacity (including owner party and sharer party) 
    # 6. hasn't expired? > not implemented right now
    
    # 1. open status
    open_request = Request.objects.filter(is_open = True)
    # 2. vehicle type (match or didn't specify)
    match_vehicle = open_request.filter(vehicle_type = Driver.objects.get(user=request.user).vehicle_type) | open_request.filter(vehicle_type = "")
    # 3. special info (match or didn't specify)
    match_special_info = match_vehicle.filter(special_request = Driver.objects.get(user=request.user).special_vehicle_info) | match_vehicle.filter(special_request = "")
    # 4. request not made by the driver
    other_user = match_special_info.exclude(owner = request.user)
    # 5. vehicle capacity (including owner party and sharer party) 
    total_pax_capacity = other_user.values("id", 
                                                "owner",
                                                "shareride__booking", 
                                                "destination", 
                                                "expected_arrival_time", 
                                                "num_passengers", 
                                                "can_share", 
                                                "is_open", 
                                                "is_complete").annotate(total_sharer = Sum("shareride__num_sharer"),
                                                                        total_pax = Sum("shareride__num_sharer") + Max("num_passengers"))
    my_request_list = total_pax_capacity.filter(total_pax__lte = Driver.objects.get(user=request.user).max_passenger_num) | total_pax_capacity.filter(total_sharer__isnull = True, num_passengers__lte=Driver.objects.get(user=request.user).max_passenger_num)
    return render(request, "ride_sharing/driver_search_for_open_request.html", {"my_request_list": my_request_list})

@login_required
def sharer_search_for_open_request(request):
    if request.method == "GET":
        return render(request, "ride_sharing/sharer_search_for_open_request.html")
    else:
        # check input data validity
        if int(request.POST["num_passengers"]) < 1:
            messages.error(request, "Number of sharer can not be less than 1. Please correct your request info and place request again.")
            return render(request, "ride_sharing/sharer_search_for_open_request.html", {"current_data" : request.POST})
        elif int(request.POST["num_passengers"]) > 5:
            messages.error(request, "Number of sharer can not be more than 5. Please correct your request info and place request again.")
            return render(request, "ride_sharing/sharer_search_for_open_request.html", {"current_data" : request.POST})
        elif request.POST["earliest_arrival_time"] > request.POST["latest_arrival_time"]:
            messages.error(request, "Earliest Arrival Time can not be later than Lateast Arrival Time. Please correct your request info and place request again.")
            return render(request, "ride_sharing/sharer_search_for_open_request.html", {"current_data" : request.POST})
                
        # filter based on:
        # 1. request is open
        # 2. ride is sharable
        # 3. destination
        # 4. arrival time window
        # 5. made by another user (it would be very confusing if we allow user to search for share ride and they found their own booking)
        # 6. number of riders (passenger + sharer) <= 6
        # 7. hasn't expired? > not implemented yet
        
        # 1 - 4 filters
        filtered_list = Request.objects.filter(is_open = True, 
                                                can_share = True, 
                                                destination=request.POST["destination"],
                                                expected_arrival_time__gte=request.POST["earliest_arrival_time"],
                                                expected_arrival_time__lte=request.POST["latest_arrival_time"])

        # 5. make by another user
        other_user = filtered_list.exclude(owner = request.user)

        # 6. number of riders
        available_slots_minus_current_request = 6 - int(request.POST["num_passengers"])
        total_pax_capacity = other_user.values("id", 
                                                "owner",
                                                "shareride__booking", 
                                                "destination", 
                                                "expected_arrival_time", 
                                                "num_passengers", 
                                                "can_share", 
                                                "is_open", 
                                                "is_complete").annotate(total_sharer = Sum("shareride__num_sharer"),
                                                                        total_pax = Sum("shareride__num_sharer") + Max("num_passengers"))
        my_request_list = total_pax_capacity.filter(total_pax__lte = available_slots_minus_current_request) | total_pax_capacity.filter(total_sharer__isnull = True, num_passengers__lte=available_slots_minus_current_request)
        
        #num_sharer here is to pass the number of sharer requested by the search to the db
        return render(request, 
                        "ride_sharing/sharer_search_result.html", 
                        {"my_request_list": my_request_list, "num_sharer": request.POST["num_passengers"]}) 

# send email section

import os.path
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Authentication and service creation
def gmail_authenticate():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    creds = None
    
    # token.json stored user access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Authentication if no valid credentials are available
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            # This credentials.json is the credential you download from Google API portal when you 
            # created the OAuth 2.0 Client IDs
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # this is the redirect URI which should match your API setting, you can 
            # find this setting in Credentials/Authorized redirect URIs at the API setting portal
            creds = flow.run_local_server(host='vcm-38185.vm.duke.edu', port=8003)
        # Save vouchers for later use
        # with open('token.json', 'w') as token:
        #     token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

# Create and send emails
def send_message(service, sender, to, subject, msg_html):
    message = MIMEMultipart('alternative')
    message['from'] = sender
    message['to'] = to
    message['subject'] = subject

    msg = MIMEText(msg_html, 'html')
    message.attach(msg)

    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}

    message = (service.users().messages().send(userId="me", body=body).execute())
    print(f"Message Id: {message['id']}")

# Using Gmail API
def send_email_test(request):
    service = gmail_authenticate()
    send_message(service, "yhece568@gmail.com", "aybucydu9@gmail.com", "Test Email - Docker", "<h1>This is a test using Gmail API</h1>")
    return HttpResponse("successfully sent email")
        