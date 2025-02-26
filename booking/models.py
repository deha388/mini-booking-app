from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError

# CustomUser modelini en başta tanımlayalım
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.username

class Facility(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=500)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.capacity < 1:
            raise ValidationError('Capacity must be positive')
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.name} ({self.location})"

    @property
    def today_booking_count(self):
        today = timezone.now().date()
        return self.bookings.filter(
            date=today,
            status__in=['confirmed', 'pending']
        ).count()

    @property
    def is_available_today(self):
        return self.today_booking_count < self.capacity

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        constraints = [
            models.UniqueConstraint(
                fields=['facility', 'date', 'start_time'],
                name='unique_booking_time_slot'
            )
        ]
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['facility', 'date']),
        ]

    def __str__(self):
        return f"{self.facility.name} - {self.date} ({self.start_time}-{self.end_time})"

    def clean(self):
        if not all([self.date, self.start_time, self.end_time, self.facility]):
            return

        # Get current time in UTC
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Check if booking is in the past
        if self.date < today:
            raise ValidationError('Cannot book in the past')
        elif self.date == today and self.start_time < current_time:
            raise ValidationError('Cannot book in the past')

        # Check if end time is after start time
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time')

        # Check for overlapping bookings
        overlapping = Booking.objects.filter(
            facility=self.facility,
            date=self.date,
            status='confirmed'
        ).exclude(id=self.id).filter(
            models.Q(start_time__lt=self.end_time) & 
            models.Q(end_time__gt=self.start_time)
        )

        if overlapping.exists():
            raise ValidationError('This time slot is already booked')

        # Check facility capacity
        concurrent_bookings = Booking.objects.filter(
            facility=self.facility,
            date=self.date,
            status='confirmed',
            start_time=self.start_time
        ).exclude(id=self.id).count()

        if concurrent_bookings >= self.facility.capacity:
            raise ValidationError('Facility is at full capacity for this time slot')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 