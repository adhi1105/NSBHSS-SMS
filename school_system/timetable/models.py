from django.db import models
from django.core.exceptions import ValidationError
from admission.models import ClassRoom
from staff.models import Staff
from school_system.models import Subject

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Removed unique=True to allow different "Period 1" timings for different sections (e.g. Primary vs High School)
    period_number = models.PositiveIntegerField(help_text="Order of the period (1, 2, 3...)")
    is_break = models.BooleanField(default=False, verbose_name="Break / Interval")

    class Meta:
        ordering = ['period_number']
        verbose_name = "Time Slot"

    def __str__(self):
        type_lbl = "Break" if self.is_break else "Period"
        return f"{type_lbl} {self.period_number} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class TimetableEntry(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ]

    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='timetable')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='timetable_entries')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)

    class Meta:
        verbose_name_plural = "Timetable Entries"
        unique_together = [
            ('classroom', 'day', 'time_slot'), # Prevent Class Conflict
            ('staff', 'day', 'time_slot'),     # Prevent Teacher Conflict
        ]

    def clean(self):
        """
        Custom Validation to provide clean error messages before saving to DB.
        """
        # 1. Check for Teacher Conflict
        # We look for ANY entry with the same Staff, Day, and Slot (excluding the current one if editing)
        teacher_conflict = TimetableEntry.objects.filter(
            staff=self.staff,
            day=self.day,
            time_slot=self.time_slot
        ).exclude(pk=self.pk)

        if teacher_conflict.exists():
            conflict_class = teacher_conflict.first().classroom.name
            raise ValidationError({
                'staff': f"{self.staff} is already teaching in {conflict_class} at this time."
            })

        # 2. Check for Room Conflict (Optional, handled by unique_together, but nicer here)
        room_conflict = TimetableEntry.objects.filter(
            classroom=self.classroom,
            day=self.day,
            time_slot=self.time_slot
        ).exclude(pk=self.pk)

        if room_conflict.exists():
            raise ValidationError({
                'time_slot': f"{self.classroom} already has a subject assigned for this period."
            })

    def save(self, *args, **kwargs):
        self.clean() # Force validation on save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.classroom} | {self.day} P{self.time_slot.period_number} | {self.subject}"