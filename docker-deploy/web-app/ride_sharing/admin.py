from django.contrib import admin
from .models import Request, Driver, ShareRide #User

# Register your models here.
# admin.site.register(User)
admin.site.register(Driver)
admin.site.register(Request)
admin.site.register(ShareRide)
