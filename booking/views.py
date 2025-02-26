from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView, DetailView, UpdateView, DeleteView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import BookingForm
from .models import Booking, Facility
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .tasks import send_booking_confirmation_email
from django.db import connections
from django.db.utils import OperationalError
from redis import Redis
from redis.exceptions import RedisError
from django.conf import settings

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('booking:home')

class CustomLogoutView(RedirectView):
    pattern_name = 'booking:home'
    
    def get(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        return super().get(request, *args, **kwargs)

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class HomeView(TemplateView):
    template_name = 'booking/home.html'

class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking:booking_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        facility_id = self.request.GET.get('facility')
        if facility_id:
            try:
                initial['facility'] = Facility.objects.get(id=facility_id)
            except Facility.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = form.save()
            # Send confirmation email asynchronously
            send_booking_confirmation_email.delay(self.object.id)
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url()
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_text()
            })
        return super().form_invalid(form)

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'booking/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-date', '-start_time']

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'booking/booking_detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        return booking.user == self.request.user

class BookingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Booking
    form_class = BookingForm
    template_name = 'booking/booking_form.html'
    success_url = reverse_lazy('booking:booking_list')

    def test_func(self):
        booking = self.get_object()
        return booking.user == self.request.user and booking.status == 'pending'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Booking updated successfully!')
        return super().form_valid(form)

class BookingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Booking
    template_name = 'booking/booking_confirm_delete.html'
    success_url = reverse_lazy('booking:booking_list')

    def test_func(self):
        booking = self.get_object()
        return booking.user == self.request.user and booking.status != 'confirmed'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Booking cancelled successfully!')
        return super().delete(request, *args, **kwargs)

def available_slots(request):
    facility_id = request.GET.get('facility')
    date = request.GET.get('date')
    
    if not facility_id or not date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    # Get all booked and pending slots for the facility and date
    booked_slots = Booking.objects.filter(
        facility_id=facility_id,
        date=date,
        status__in=['confirmed', 'pending']  # Hem onaylı hem bekleyen bookingleri kontrol et
    ).values_list('start_time', flat=True)
    
    # Convert time objects to string format
    booked_slots = [t.strftime('%H:%M') for t in booked_slots]
    
    return JsonResponse({'booked_slots': booked_slots})

class FacilityListView(ListView):
    model = Facility
    template_name = 'booking/facility_list.html'
    context_object_name = 'facilities'

    def get_queryset(self):
        return Facility.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Bugünün tüm onaylanmış VE bekleyen bookinglerini tek sorguda al
        today_bookings = Booking.objects.filter(
            date=today,
            status__in=['confirmed', 'pending']  # Hem onaylı hem bekleyen bookingleri dahil et
        ).select_related('facility')
        
        # Her facility için booking sayısını hesapla
        booking_counts = {}
        for booking in today_bookings:
            if booking.facility_id not in booking_counts:
                booking_counts[booking.facility_id] = 1
            else:
                booking_counts[booking.facility_id] += 1

        # Her facility için booking sayısını ve durumunu ayarla
        for facility in context['facilities']:
            facility.today_bookings = booking_counts.get(facility.id, 0)
            facility.is_available = facility.capacity > facility.today_bookings
        
        return context 

def health_check(request):
    # Check database connection
    db_healthy = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_healthy = False
    
    # Check Redis connection
    redis_healthy = True
    try:
        redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
    except RedisError:
        redis_healthy = False
    
    status = 200 if (db_healthy and redis_healthy) else 503
    
    health_status = {
        'status': 'healthy' if status == 200 else 'unhealthy',
        'database': 'up' if db_healthy else 'down',
        'redis': 'up' if redis_healthy else 'down',
    }
    
    return JsonResponse(health_status, status=status) 