from django.urls import path

from . import views

app_name = "ride_sharing"
urlpatterns = [
    path("", views.homepage, name="homepage"),
    #path("send_email_test/", views.send_email_test, name="send_email_test"),
    path("user_register/", views.user_register, name="user_register"),
    # user request related
    path("place_request/", views.place_request, name="place_request"),
    path("my_requests/", views.my_requests, name="my_requests"),
    path("view_request_detail", views.view_request_detail, name="view_request_detail"),
    path("edit_request_detail_owner", views.edit_request_detail_owner, name="edit_request_detail_owner"),
    path("edit_request_detail_sharer", views.edit_request_detail_sharer, name="edit_request_detail_sharer"),
    # driver related
    path("driver_view_confirmed_requests/", views.driver_view_confirmed_requests, name="driver_view_confirmed_requests"),
    path("driver_registration/", views.driver_registration, name="driver_registration"),
    path("driver_profile/", views.driver_profile, name="driver_profile"),
    path("edit_driver_profile/", views.edit_driver_profile, name="edit_driver_profile"),
    path("driver_registration_result/", views.driver_registration_result, name="driver_registration_result"),
    path("driver_search_for_open_request/", views.driver_search_for_open_request, name="driver_search_for_open_request"),
    # sharer related
    path("sharer_search_for_open_request/", views.sharer_search_for_open_request, name="sharer_search_for_open_request"),
]