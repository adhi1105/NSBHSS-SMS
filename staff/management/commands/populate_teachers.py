from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError
from staff.models import Staff, SubjectAllocation, Department
from admission.models import ClassRoom
from school_system.models import Subject
import random

class Command(BaseCommand):
    help = 'Populates 32 teachers with precise Batch Code logic and updates existing profiles'

    def handle(self, *args, **kwargs):
        # 1. FACULTY DATA
        faculty_data = [
            ("Anjali", "Menon", "English"), ("Biju", "Balakrishnan", "English"),
            ("Preethi", "Chandran", "English"), ("Sreedevi", "Amma", "Malayalam"),
            ("Nandini", "Varma", "Malayalam"), ("Priya", "Raghavan", "Hindi"),
            ("Hussain", "Musliyar", "Arabic"),
            ("Suresh", "Kumar V.", "Biology"), ("Raji", "Viswanath", "Biology"),
            ("Deepa", "Panicker", "Computer Science"), ("Mathew", "Scaria", "Computer Science"),
            ("Kurien", "Thomas", "Physics"), ("Jacob", "Punnoose", "Physics"),
            ("Fathima", "Beevi", "Chemistry"), ("Reshma", "K.", "Chemistry"),
            ("Mohandas", "Nair", "Mathematics"), ("Latha", "Mahesh", "Mathematics"),
            ("Suresh", "Pillai", "Mathematics"),
            ("Gopika", "Parameshwaran", "Accountancy"), ("K.P.", "Narayanan", "Accountancy"),
            ("Aswathy", "Menon", "Business Studies"), ("Siddharth", "Pillai", "Business Studies"),
            ("Sooraj", "S.", "Computer Application"), 
            ("Philipose", "Marar", "History"), ("Sarah", "Joseph", "History"),
            ("K.R.", "Gowri", "Political Science"), ("P.J.", "Joseph", "Political Science"),
            ("Rema", "Devi", "Sociology"), ("Abdul", "Rasheed", "Geography"),
            ("Varghese", "Mathew", "Economics"), ("Sreejith", "K.V.", "Economics"),
            ("Vinod", "Gopinath", "Physical Education")
        ]

        self.stdout.write(self.style.WARNING(f"Initializing Faculty Allocation..."))

        teacher_group, _ = Group.objects.get_or_create(name='Teacher')
        
        # Ensure 'General' department exists as a fallback, or create specific ones if you have them
        general_dept, _ = Department.objects.get_or_create(name="General")

        classrooms = list(ClassRoom.objects.all())
        if not classrooms:
            self.stdout.write(self.style.ERROR("No Classrooms found! Run populate_classes first."))
            return

        count = 0
        
        for first, last, sub_name in faculty_data:
            # A. User Creation (Get or Create)
            username = f"{first.lower()}{last.lower().replace('.', '').replace(' ', '')}"
            user, created = User.objects.get_or_create(
                username=username, 
                defaults={'first_name': first, 'last_name': last, 'email': f"{username}@school.com", 'is_staff': True}
            )
            
            if created:
                user.set_password("kerala@123")
                user.groups.add(teacher_group)
                user.save()

            # B. Staff Profile (Update or Create) - KEY CHANGE HERE
            # We use update_or_create so Anjali gets upgraded from 'General' to 'HSST English'
            staff, _ = Staff.objects.update_or_create(
                user=user, 
                defaults={
                    'designation': f"HSST {sub_name}", 
                    'staff_id': f"T26-{100+count}",
                    'department': general_dept, # Or map this to real Departments if you have them
                    'status': 'active',
                    'is_teaching_staff': True
                }
            )
            
            # Create Subject
            subject, _ = Subject.objects.get_or_create(name=sub_name)

            # C. PRECISE MAPPING LOGIC
            target_prefixes = []
            if sub_name in ["English", "Malayalam", "Hindi", "Arabic", "Physical Education"]:
                target_prefixes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
            elif sub_name in ["Physics", "Chemistry"]:
                target_prefixes = ['A', 'B', 'C', 'D', 'H', 'E', 'F', 'G']
            elif sub_name == "Mathematics":
                target_prefixes = ['A', 'B', 'C', 'D', 'H', 'F', 'G']
            elif sub_name == "Biology":
                target_prefixes = ['A', 'B', 'C', 'D', 'H']
            elif sub_name == "Computer Science":
                target_prefixes = ['F', 'G']
            elif sub_name in ["Accountancy", "Business Studies", "Computer Application"]:
                target_prefixes = ['J', 'K']
            elif sub_name in ["History", "Political Science", "Sociology", "Geography"]:
                target_prefixes = ['I']
            elif sub_name == "Economics":
                target_prefixes = ['J', 'K', 'I']

            # D. Filter & Assign
            eligible_classes = [c for c in classrooms if any(c.name.startswith(p) for p in target_prefixes)]
            selection = [] # Initialize safely

            if eligible_classes:
                random.shuffle(eligible_classes)
                selection = eligible_classes[:3] 
                
                for cls in selection:
                    try:
                        SubjectAllocation.objects.get_or_create(staff=staff, subject=subject, classroom=cls)
                    except IntegrityError:
                        pass 

            count += 1
            self.stdout.write(f"  > {first} {last} ({sub_name}) -> Updated & Assigned to {len(selection)} classes")

        self.stdout.write(self.style.SUCCESS(f"Successfully configured {count} teachers."))