import datetime
from .models import Student

def generate_student_id():
    """Generates a unique ID like STU-2024-0001"""
    current_year = datetime.date.today().year
    # Count how many students registered this year
    count = Student.objects.filter(admission_date__year=current_year).count()
    # Format: Prefix - Year - Sequence (padded with zeros)
    return f"STU-{current_year}-{count + 1:04d}"