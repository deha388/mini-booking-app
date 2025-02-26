from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, Facility
from django.db import models
from datetime import datetime, time

class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Select the date for your booking'
    )
    
    start_time = forms.ChoiceField(
        choices=[],  # Choices will be set in __init__
        help_text='Select start time'
    )

    class Meta:
        model = Booking
        fields = ['facility', 'date', 'start_time', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Generate time slots (9:00 to 18:00)
        time_slots = []
        for hour in range(9, 18):
            time_str = f"{hour:02d}:00"
            time_slots.append((time_str, time_str))
        
        self.fields['start_time'].choices = time_slots
        
        # Only show available facilities
        self.fields['facility'].queryset = Facility.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        facility = cleaned_data.get('facility')

        if date and start_time and facility:
            try:
                # Convert start_time string to time object
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                # Calculate end_time (1 hour after start_time)
                end_hour = (start_time_obj.hour + 1) % 24
                end_time = time(end_hour, 0)
                
                # Get current time in UTC
                now = timezone.now()
                today = now.date()
                current_time = now.time()
                
                # Compare dates
                if date < today:
                    raise ValidationError('Cannot book in the past')
                elif date == today and start_time_obj < current_time:
                    raise ValidationError('Cannot book in the past')

                # Check for overlapping bookings
                overlapping = Booking.objects.filter(
                    facility=facility,
                    date=date,
                    status__in=['confirmed', 'pending']
                ).filter(
                    models.Q(start_time__lt=end_time) & 
                    models.Q(end_time__gt=start_time_obj)
                )

                if overlapping.exists():
                    raise ValidationError(
                        'This time slot is already booked or pending. Please choose another time.'
                    )

                # Check facility capacity
                concurrent_bookings = Booking.objects.filter(
                    facility=facility,
                    date=date,
                    status__in=['confirmed', 'pending'],
                    start_time=start_time_obj
                ).count()

                if concurrent_bookings >= facility.capacity:
                    raise ValidationError(
                        'Facility is at full capacity for this time slot.'
                    )

                # Add end_time to cleaned_data
                cleaned_data['end_time'] = end_time

            except (ValueError, TypeError) as e:
                raise ValidationError(f'Invalid date or time format: {str(e)}')

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.user = self.user
        booking.end_time = self.cleaned_data['end_time']
        if commit:
            booking.save()
        return booking 