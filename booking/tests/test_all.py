from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, time
from booking.models import Facility, Booking
from booking.forms import BookingForm
from django.contrib import messages
from django.contrib.messages import get_messages

User = get_user_model()

class FacilityModelTests(TestCase):
    def setUp(self):
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2,
            description='Test Description'
        )

    def test_facility_creation(self):
        self.assertEqual(self.facility.name, 'Test Facility')
        self.assertEqual(self.facility.capacity, 2)

    def test_negative_capacity(self):
        with self.assertRaises(ValidationError):
            facility = Facility(
                name='Invalid Facility',
                location='Test Location',
                capacity=-1
            )
            facility.full_clean()

    def test_str_representation(self):
        self.assertEqual(
            str(self.facility),
            'Test Facility (Test Location)'
        )

    def test_today_booking_count(self):
        user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        today = timezone.now().date()
        
        # Create two bookings for today
        Booking.objects.create(
            user=user,
            facility=self.facility,
            date=today,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        Booking.objects.create(
            user=user,
            facility=self.facility,
            date=today,
            start_time='11:00',
            end_time='12:00',
            status='pending'
        )
        
        self.assertEqual(self.facility.today_booking_count, 2)

    def test_is_available_today(self):
        """Test facility availability check"""
        user = User.objects.create_user('testuser2', 'test2@test.com', 'testpass')
        today = timezone.now().date()
        
        # Create bookings up to capacity
        for i in range(self.facility.capacity):
            Booking.objects.create(
                user=user,
                facility=self.facility,
                date=today,
                start_time=f'{10+i}:00',
                end_time=f'{11+i}:00',
                status='confirmed'
            )
        
        self.assertFalse(self.facility.is_available_today)

class BookingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_booking_creation(self):
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.user, self.user)

    def test_past_booking_validation(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            booking = Booking(
                user=self.user,
                facility=self.facility,
                date=yesterday,
                start_time='10:00',
                end_time='11:00'
            )
            booking.full_clean()

    def test_booking_str_representation(self):
        """Test booking string representation"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        expected = f"{self.facility.name} - {self.tomorrow} (10:00:00-11:00:00)"
        self.assertEqual(str(booking), expected)

class BookingFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_valid_form(self):
        form_data = {
            'facility': self.facility.id,
            'date': self.tomorrow,
            'start_time': '10:00',
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_past_date(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        form_data = {
            'facility': self.facility.id,
            'date': yesterday,
            'start_time': '10:00'
        }
        form = BookingForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('Cannot book in the past', str(form.errors))

    def test_overlapping_booking_validation(self):
        """Test that overlapping bookings are not allowed"""
        # Create first booking
        Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )

        # Try to create overlapping booking
        form_data = {
            'facility': self.facility.id,
            'date': self.tomorrow,
            'start_time': '10:00',  # Aynı saati kullan
            'notes': 'Second booking'
        }
        form = BookingForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('This time slot is already booked', str(form.errors))

    def test_booking_update_view_wrong_user(self):
        """Test that users cannot update other users' bookings"""
        other_user = User.objects.create_user('otheruser', 'other@test.com', 'otherpass')
        booking = Booking.objects.create(
            user=other_user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_update', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 403)  # Should return Forbidden

    def test_booking_delete_view_confirmed_booking(self):
        """Test that confirmed bookings cannot be deleted"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('booking:booking_delete', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 403)  # Should return Forbidden

    def test_booking_detail_view(self):
        """Test booking detail view"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_detail', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_detail.html')

    def test_available_slots_api(self):
        """Test available slots API"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:available_slots'),
            {'facility': self.facility.id, 'date': self.tomorrow}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'booked_slots': []})

    def test_available_slots_api_with_bookings(self):
        """Test available slots API with existing bookings"""
        Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:available_slots'),
            {'facility': self.facility.id, 'date': self.tomorrow}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'booked_slots': ['10:00']})

    def test_available_slots_api_missing_params(self):
        """Test available slots API with missing parameters"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('booking:available_slots'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Missing parameters'})

    def test_booking_update_view_invalid_form(self):
        """Test booking update with invalid form data"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        form_data = {
            'facility': self.facility.id,
            'date': 'invalid-date',  # Invalid date format
            'start_time': '11:00'
        }
        response = self.client.post(
            reverse('booking:booking_update', kwargs={'pk': booking.pk}),
            form_data
        )
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_booking_create_view_invalid_form(self):
        """Test booking creation with invalid form data"""
        self.client.login(username='testuser', password='testpass')
        form_data = {
            'facility': self.facility.id,
            'date': 'invalid-date',  # Invalid date format
            'start_time': '10:00'
        }
        response = self.client.post(reverse('booking:booking_create'), form_data)
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_logout_view(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('booking:logout'))
        self.assertEqual(response.status_code, 302)  # Redirects to home
        self.assertFalse('_auth_user_id' in self.client.session)  # User is logged out

    def test_booking_create_view_with_facility(self):
        """Test booking creation with pre-selected facility"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_create'),
            {'facility': self.facility.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].initial['facility'],
            self.facility
        )

    def test_booking_create_view_invalid_facility(self):
        """Test booking creation with invalid facility id"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_create'),
            {'facility': 999}  # Non-existent facility id
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('facility', response.context['form'].initial)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_home_view(self):
        response = self.client.get(reverse('booking:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/home.html')

    def test_facility_list_view(self):
        response = self.client.get(reverse('booking:facility_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/facility_list.html')
        self.assertContains(response, self.facility.name)

    def test_booking_list_view_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('booking:booking_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_list.html')

    def test_booking_list_view_unauthenticated(self):
        response = self.client.get(reverse('booking:booking_list'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_booking_create_view_unauthenticated(self):
        """Test that unauthenticated users cannot create bookings"""
        response = self.client.get(reverse('booking:booking_create'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_booking_create_view_authenticated(self):
        """Test booking creation with authenticated user"""
        self.client.login(username='testuser', password='testpass')
        form_data = {
            'facility': self.facility.id,
            'date': self.tomorrow,
            'start_time': '10:00',
            'notes': 'Test booking'
        }
        response = self.client.post(reverse('booking:booking_create'), form_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after success
        self.assertTrue(Booking.objects.exists())

    def test_booking_update_view_wrong_user(self):
        """Test that users cannot update other users' bookings"""
        other_user = User.objects.create_user('otheruser', 'other@test.com', 'otherpass')
        booking = Booking.objects.create(
            user=other_user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_update', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 403)  # Should return Forbidden

    def test_booking_delete_view_confirmed_booking(self):
        """Test that confirmed bookings cannot be deleted"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(
            reverse('booking:booking_delete', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 403)  # Should return Forbidden

    def test_booking_detail_view(self):
        """Test booking detail view"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_detail', kwargs={'pk': booking.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'booking/booking_detail.html')

    def test_available_slots_api(self):
        """Test available slots API"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:available_slots'),
            {'facility': self.facility.id, 'date': self.tomorrow}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'booked_slots': []})

    def test_available_slots_api_with_bookings(self):
        """Test available slots API with existing bookings"""
        Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00',
            status='confirmed'
        )
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:available_slots'),
            {'facility': self.facility.id, 'date': self.tomorrow}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'booked_slots': ['10:00']})

    def test_available_slots_api_missing_params(self):
        """Test available slots API with missing parameters"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('booking:available_slots'))
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'Missing parameters'})

    def test_booking_update_view_invalid_form(self):
        """Test booking update with invalid form data"""
        booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=self.tomorrow,
            start_time='10:00',
            end_time='11:00'
        )
        self.client.login(username='testuser', password='testpass')
        form_data = {
            'facility': self.facility.id,
            'date': 'invalid-date',  # Invalid date format
            'start_time': '11:00'
        }
        response = self.client.post(
            reverse('booking:booking_update', kwargs={'pk': booking.pk}),
            form_data
        )
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_booking_create_view_invalid_form(self):
        """Test booking creation with invalid form data"""
        self.client.login(username='testuser', password='testpass')
        form_data = {
            'facility': self.facility.id,
            'date': 'invalid-date',  # Invalid date format
            'start_time': '10:00'
        }
        response = self.client.post(reverse('booking:booking_create'), form_data)
        self.assertEqual(response.status_code, 200)  # Returns form with errors
        self.assertTemplateUsed(response, 'booking/booking_form.html')

    def test_logout_view(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('booking:logout'))
        self.assertEqual(response.status_code, 302)  # Redirects to home
        self.assertFalse('_auth_user_id' in self.client.session)  # User is logged out

    def test_booking_create_view_with_facility(self):
        """Test booking creation with pre-selected facility"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_create'),
            {'facility': self.facility.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].initial['facility'],
            self.facility
        )

    def test_booking_create_view_invalid_facility(self):
        """Test booking creation with invalid facility id"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(
            reverse('booking:booking_create'),
            {'facility': 999}  # Non-existent facility id
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('facility', response.context['form'].initial)

class AdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            'admin', 'admin@test.com', 'adminpass'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')
        self.facility = Facility.objects.create(
            name='Test Facility',
            location='Test Location',
            capacity=2
        )
        self.user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        self.booking = Booking.objects.create(
            user=self.user,
            facility=self.facility,
            date=timezone.now().date() + timedelta(days=1),
            start_time='10:00',
            end_time='11:00'
        )
        self.tomorrow = timezone.now().date() + timedelta(days=1)

    def test_facility_admin(self):
        """Test facility admin list view"""
        response = self.client.get(reverse('admin:booking_facility_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_booking_admin(self):
        """Test booking admin list view"""
        response = self.client.get(reverse('admin:booking_booking_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_booking_admin_actions(self):
        """Test booking admin actions"""
        # Test confirm action
        response = self.client.post(
            reverse('admin:booking_booking_changelist'),
            {
                'action': 'confirm_bookings',
                '_selected_action': [self.booking.pk],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

        # Test cancel action
        response = self.client.post(
            reverse('admin:booking_booking_changelist'),
            {
                'action': 'cancel_bookings',
                '_selected_action': [self.booking.pk],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_facility_admin_search(self):
        """Test facility admin search functionality"""
        response = self.client.get(
            reverse('admin:booking_facility_changelist'),
            {'q': 'Test'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.facility.name)

    def test_booking_admin_filters(self):
        """Test booking admin filters"""
        response = self.client.get(
            reverse('admin:booking_booking_changelist'),
            {'status': 'pending'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.facility.name)

    def test_facility_admin_detail(self):
        """Test facility admin detail view"""
        response = self.client.get(
            reverse('admin:booking_facility_change', args=[self.facility.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.facility.name)

    def test_booking_admin_detail(self):
        """Test booking admin detail view"""
        response = self.client.get(
            reverse('admin:booking_booking_change', args=[self.booking.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.facility.name)

class ManagementTests(TestCase):
    def test_main_with_error(self):
        """Test manage.py main function with error"""
        from manage import main
        import sys
        from unittest.mock import patch
        
        with patch.object(sys, 'argv', ['manage.py', 'invalid_command']):
            with self.assertRaises(SystemExit):
                main()