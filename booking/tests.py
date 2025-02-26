from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Facility, Booking
from django.core.exceptions import ValidationError
from .forms import BookingForm

User = get_user_model()

class BookingSystemTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        
        # Create test facility
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2,
            description='Test Description'
        )
        
        # Set up test client
        self.client = Client()

    def test_user_registration(self):
        """Test user registration functionality"""
        response = self.client.post(reverse('booking:signup'), {
            'username': 'newuser',
            'password1': 'complex_password123',
            'password2': 'complex_password123',
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login functionality"""
        response = self.client.post(reverse('booking:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful login
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_facility_model(self):
        """Test Facility model"""
        self.assertEqual(str(self.facility), 'Test Facility (Test Location)')
        self.assertTrue(self.facility.is_available(timezone.now().date()))

    def test_booking_creation(self):
        """Test booking creation"""
        self.client.login(username='testuser', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'facility': self.facility.id,
            'date': tomorrow,
            'start_time': '10:00',
            'end_time': '11:00',
            'notes': 'Test booking'
        }
        
        response = self.client.post(reverse('booking:booking_create'), booking_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful booking
        self.assertTrue(Booking.objects.filter(user=self.user, facility=self.facility).exists())

    def test_booking_validation(self):
        """Test booking validation rules"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test past date booking
        yesterday = timezone.now().date() - timedelta(days=1)
        past_booking_data = {
            'facility': self.facility.id,
            'date': yesterday,
            'start_time': '10:00',
            'end_time': '11:00',
        }
        
        response = self.client.post(reverse('booking:booking_create'), past_booking_data)
        self.assertEqual(response.status_code, 200)  # Should stay on same page with errors
        self.assertFalse(Booking.objects.filter(date=yesterday).exists())

        # Test invalid time range
        tomorrow = timezone.now().date() + timedelta(days=1)
        invalid_time_data = {
            'facility': self.facility.id,
            'date': tomorrow,
            'start_time': '11:00',
            'end_time': '10:00',
        }
        
        response = self.client.post(reverse('booking:booking_create'), invalid_time_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.filter(
            start_time='11:00',
            end_time='10:00'
        ).exists())

    def test_booking_capacity(self):
        """Test facility capacity limits"""
        self.client.login(username='testuser', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Create first booking
        booking1 = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )

        # Create second booking with different time
        booking2 = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=tomorrow,
            start_time='11:00',  # Different time
            end_time='12:00',
            status='confirmed'
        )
        
        # Try to create a third booking
        booking_data = {
            'facility': self.facility.id,
            'date': tomorrow,
            'start_time': '10:00',
            'end_time': '11:00',
        }
        
        response = self.client.post(reverse('booking:booking_create'), booking_data)
        self.assertEqual(response.status_code, 200)  # Should stay on same page with errors
        self.assertEqual(
            Booking.objects.filter(
                date=tomorrow,
                status='confirmed'
            ).count(),
            2  # Should still only have 2 bookings
        )

    def test_home_page(self):
        """Test home page accessibility"""
        response = self.client.get(reverse('booking:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/home.html')

    def test_authenticated_views(self):
        """Test views that require authentication"""
        booking_create_url = reverse('booking:booking_create')
        
        # Test without authentication
        response = self.client.get(booking_create_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        
        # Test with authentication
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(booking_create_url)
        self.assertEqual(response.status_code, 200)

class FacilityModelTests(TestCase):
    def test_negative_capacity(self):
        """Test that capacity cannot be negative"""
        with self.assertRaises(ValidationError):
            facility = Facility(
                name="Test Facility",
                location="Test Location",
                capacity=-1
            )
            facility.full_clean()

    def test_optional_description(self):
        """Test that description is optional"""
        facility = Facility.objects.create(
            name="Test Facility",
            location="Test Location",
            capacity=1
        )
        self.assertEqual(facility.description, "")

    def test_is_available_method(self):
        """Test is_available method with different scenarios"""
        facility = Facility.objects.create(
            name="Test Facility",
            location="Test Location",
            capacity=2
        )
        user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        date = timezone.now().date() + timedelta(days=1)

        # Should be available initially
        self.assertTrue(facility.is_available(date))

        # Create one booking
        Booking.objects.create(
            user=user,
            facility=facility,
            date=date,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        # Should still be available (capacity is 2)
        self.assertTrue(facility.is_available(date))

        # Create second booking
        Booking.objects.create(
            user=user,
            facility=facility,
            date=date,
            start_time='11:00',
            end_time='12:00',
            status='confirmed'
        )
        # Should now be unavailable (at capacity)
        self.assertFalse(facility.is_available(date))

class BookingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.facility = Facility.objects.create(
            name="Test Facility",
            location="Test Location",
            capacity=2
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_booking_status_changes(self):
        """Test booking status transitions"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.assertEqual(booking.status, 'pending')  # Default status

        booking.status = 'confirmed'
        booking.save()
        self.assertEqual(booking.status, 'confirmed')

    def test_overlapping_bookings(self):
        """Test that overlapping bookings are prevented"""
        # İlk booking'i oluştur
        Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )

        # Çakışan booking'i dene
        with self.assertRaises(ValidationError):
            booking2 = Booking(
                user=self.user,
                facility=self.facility,
                date=self.tomorrow,
                start_time='10:30',  # Overlapping time
                end_time='11:30',
                status='confirmed'
            )
            booking2.full_clean()  # Bu ValidationError raise etmeli

class BookingFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.facility = Facility.objects.create(
            name="Test Facility",
            location="Test Location",
            capacity=1
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)  # Yarının tarihini al

    def test_invalid_date_format(self):
        """Test form validation with invalid date format"""
        form_data = {
            'facility': self.facility.id,
            'date': 'invalid-date',
            'start_time': '10:00',
            'end_time': '11:00'
        }
        form = BookingForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_full_capacity_validation(self):
        """Test form validation when facility is at capacity"""
        # Create a booking that fills the capacity
        Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,  # Sabit tarih yerine dinamik tarih kullan
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )

        # Try to create another booking for the same time
        form_data = {
            'facility': self.facility.id,
            'date': self.tomorrow,  # Sabit tarih yerine dinamik tarih kullan
            'start_time': '10:00',
            'end_time': '11:00'
        }
        form = BookingForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)  # Genel hata mesajını kontrol et 

class BookingViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass123')
        self.other_user = User.objects.create_user('otheruser', 'other@test.com', 'otherpass123')
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create a test booking
        self.booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='pending'
        )

    def test_booking_list_view(self):
        """Test booking list view"""
        response = self.client.get(reverse('booking:booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_list.html')
        self.assertContains(response, self.booking.facility.name)

    def test_booking_detail_view(self):
        """Test booking detail view"""
        response = self.client.get(
            reverse('booking:booking_detail', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_detail.html')
        self.assertContains(response, self.booking.facility.name)

    def test_booking_update_view(self):
        """Test booking update view"""
        update_data = {
            'facility': self.facility.id,
            'date': self.tomorrow,
            'start_time': '11:00',
            'end_time': '12:00',
            'notes': 'Updated booking'
        }
        response = self.client.post(
            reverse('booking:booking_update', kwargs={'pk': self.booking.pk}),
            update_data
        )
        self.assertEqual(response.status_code, 302)  # Should redirect after successful update
        self.booking.refresh_from_db()
        self.assertEqual(str(self.booking.start_time), '11:00:00')

    def test_booking_delete_view(self):
        """Test booking delete view"""
        response = self.client.post(
            reverse('booking:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 302)  # Should redirect after successful delete
        self.assertFalse(
            Booking.objects.filter(pk=self.booking.pk).exists()
        )

    def test_other_user_cannot_access(self):
        """Test that users cannot access other users' bookings"""
        self.client.logout()
        self.client.login(username='otheruser', password='otherpass123')
        
        # Try to access detail view
        response = self.client.get(
            reverse('booking:booking_detail', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)  # Should return Forbidden

        # Try to update
        response = self.client.get(
            reverse('booking:booking_update', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403)

        # Try to delete
        response = self.client.get(
            reverse('booking:booking_delete', kwargs={'pk': self.booking.pk})
        )
        self.assertEqual(response.status_code, 403) 