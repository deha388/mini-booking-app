from django.contrib import admin
from .models import Facility, Booking, CustomUser
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'created_at')
    list_filter = ('location',)
    search_fields = ('name', 'location')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'capacity', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('facility', 'user', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'facility')
    search_fields = ('facility__name', 'user__username')
    ordering = ('-date', '-start_time')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('facility', 'user')

    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'facility', 'date', 'start_time', 'end_time', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time Slot'

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def facility_link(self, obj):
        url = reverse('admin:booking_facility_change', args=[obj.facility.id])
        return format_html('<a href="{}">{}</a>', url, obj.facility.name)
    facility_link.short_description = 'Facility'

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new record
            if not obj.user:
                obj.user = request.user
        super().save_model(request, obj, form, change)

    actions = ['confirm_bookings', 'cancel_bookings']

    def confirm_bookings(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} bookings were confirmed.')
    confirm_bookings.short_description = 'Mark selected bookings as confirmed'

    def cancel_bookings(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} bookings were cancelled.')
    cancel_bookings.short_description = 'Mark selected bookings as cancelled'

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',) 