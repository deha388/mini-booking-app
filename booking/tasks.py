from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_booking_confirmation_email(booking_id):
    from .models import Booking
    try:
        booking = Booking.objects.get(id=booking_id)
        subject = f'Booking Confirmation - {booking.facility.name}'
        message = f"""
        Dear {booking.user.username},

        Your booking has been confirmed:
        Facility: {booking.facility.name}
        Date: {booking.date}
        Time: {booking.start_time} - {booking.end_time}

        Thank you for using our service!
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False 