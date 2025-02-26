from django.core.management.base import BaseCommand
from booking.models import Facility

class Command(BaseCommand):
    help = 'Creates sample facilities'

    def handle(self, *args, **kwargs):
        # Eğer hiç facility yoksa oluştur
        if not Facility.objects.exists():
            facilities = [
                {
                    'name': 'Swimming Pool',
                    'location': 'Ground Floor',
                    'capacity': 20,
                    'description': 'Olympic size swimming pool'
                },
                {
                    'name': 'Tennis Court',
                    'location': 'Outdoor Area',
                    'capacity': 4,
                    'description': 'Professional tennis court'
                },
                {
                    'name': 'Gym',
                    'location': 'First Floor',
                    'capacity': 30,
                    'description': 'Fully equipped gym'
                },
                {
                    'name': 'Yoga Studio',
                    'location': 'Second Floor',
                    'capacity': 15,
                    'description': 'Peaceful yoga studio'
                }
            ]
            
            for facility_data in facilities:
                Facility.objects.create(**facility_data)
            
            self.stdout.write(self.style.SUCCESS('Successfully created sample facilities'))
        else:
            self.stdout.write(self.style.SUCCESS('Facilities already exist, skipping creation')) 