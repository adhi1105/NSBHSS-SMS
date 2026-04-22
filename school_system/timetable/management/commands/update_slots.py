from django.core.management.base import BaseCommand
from timetable.models import TimeSlot

class Command(BaseCommand):
    help = 'Updates timetable slots to 3-2-2-2 order with specific breaks'

    def handle(self, *args, **kwargs):
        TimeSlot.objects.all().delete()
        
        slots = [
            # Morning Session (3 Periods)
            {'n': 1, 's': "09:00", 'e': "09:45", 'b': False},
            {'n': 2, 's': "09:45", 'e': "10:30", 'b': False},
            {'n': 3, 's': "10:30", 'e': "11:15", 'b': False},
            {'n': 0, 's': "11:15", 'e': "11:30", 'b': True}, # Morning Break
            
            # Mid-Day Session (2 Periods)
            {'n': 4, 's': "11:30", 'e': "12:05", 'b': False},
            {'n': 5, 's': "12:05", 'e': "12:45", 'b': False},
            {'n': 0, 's': "12:45", 'e': "13:20", 'b': True}, # Lunch
            
            # Afternoon Session 1 (2 Periods)
            {'n': 6, 's': "13:20", 'e': "14:05", 'b': False},
            {'n': 7, 's': "14:05", 'e': "14:50", 'b': False},
            {'n': 0, 's': "14:50", 'e': "15:00", 'b': True}, # Afternoon Break
            
            # Afternoon Session 2 (2 Periods)
            {'n': 8, 's': "15:00", 'e': "15:40", 'b': False},
            {'n': 9, 's': "15:40", 'e': "16:20", 'b': False},
        ]

        for item in slots:
            TimeSlot.objects.create(
                period_number=item['n'],
                start_time=item['s'],
                end_time=item['e'],
                is_break=item['b']
            )
        
        self.stdout.write(self.style.SUCCESS("✅ Timetable structure updated to 3-2-2-2 order."))