from django.urls import path
from .views import (
    CustomLoginView, CustomLogoutView, SignUpView, HomeView,
    BookingListView, BookingDetailView, BookingCreateView,
    BookingUpdateView, BookingDeleteView, available_slots, FacilityListView,
    health_check
)

app_name = 'booking'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),
    path('booking/<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path('booking/create/', BookingCreateView.as_view(), name='booking_create'),
    path('booking/<int:pk>/update/', BookingUpdateView.as_view(), name='booking_update'),
    path('booking/<int:pk>/delete/', BookingDeleteView.as_view(), name='booking_delete'),
    path('api/available-slots/', available_slots, name='available_slots'),
    path('facilities/', FacilityListView.as_view(), name='facility_list'),
    path('health/', health_check, name='health_check'),
] 