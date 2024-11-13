import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
# from django.contrib.auth.models import User

# Create your models here.
# class User(models.Model):
#     # email = models.CharField(max_length=200)
#     registration_date = models.DateTimeField("date registered")
#     def __str__(self):
#         return str(self.id)

class Driver(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    vehicle_type = models.CharField(max_length=200)
    license_plate_num = models.CharField(max_length=50)
    max_passenger_num = models.IntegerField()
    special_vehicle_info = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return self.name
    
class Request(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, models.SET_NULL, blank=True, null=True)
    destination = models.CharField(max_length=200)
    expected_arrival_time = models.DateTimeField(auto_now=False, auto_now_add=False)
    num_passengers = models.IntegerField(default=1)
    vehicle_type = models.CharField(max_length=200, blank=True)
    special_request = models.TextField(blank=True)
    can_share = models.BooleanField()
    is_open = models.BooleanField()
    is_complete = models.BooleanField()
    def __str__(self):
        return self.destination

class ShareRide(models.Model):
    sharer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking = models.ForeignKey(Request, on_delete=models.CASCADE)
    num_sharer = models.IntegerField(default=1)
    def __str__(self):
        return self.sharer.username
