import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from staff.models import Staff, SubjectAllocation, Department
from admission.models import ClassRoom
from school_system.models import Subject

class Command(BaseCommand):
    help = 'Wipes data, deletes old buggy users, and populates 50 teachers perfectly'

    def handle(self, *args, **kwargs):
        STREAM_MAPPING = {
            'Home Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam/Hindi', 'Home Science'],
            'Biology Science': ['Physics', 'Chemistry', 'Biology', 'English', 'Malayalam/Hindi', 'Mathematics'],
            'Computer Science': ['Physics', 'Chemistry', 'English', 'Malayalam/Hindi', 'Computer Science', 'Mathematics'],
            'Commerce': ['Accountancy', 'Business Studies', 'Economics', 'English', 'Malayalam/Hindi'],
            'Humanities': ['History', 'Economics', 'Political Science', 'Sociology', 'English', 'Malayalam/Hindi']
        }

        faculty_pool = [
            ("Anjali", "Menon", "English"), ("Biju", "Balakrishnan", "English"), ("Preethi", "Chandran", "English"), 
            ("Deepak", "Nair", "English"), ("Saritha", "Vinod", "English"), ("Gautham", "Krishna", "English"),
            ("Sreedevi", "Amma", "Malayalam"), ("Nandini", "Varma", "Malayalam"), 
            ("Pradeep", "Kumar", "Malayalam"), ("Remya", "Krishnan", "Malayalam"),
            ("Priya", "Raghavan", "Hindi"), ("Sunitha", "Devi", "Hindi"), 
            ("Vishnu", "Prasad", "Hindi"), ("Maya", "Ramesh", "Hindi"),
            ("Suresh", "Kumar V.", "Biology"), ("Raji", "Viswanath", "Biology"), ("Meera", "Sankar", "Biology"), ("Anil", "Bhaskar", "Biology"),
            ("Deepa", "Panicker", "Computer Science"), ("Mathew", "Scaria", "Computer Science"), ("Arjun", "Das", "Computer Science"), ("Sneha", "Prakash", "Computer Science"),
            ("Kurien", "Thomas", "Physics"), ("Jacob", "Punnoose", "Physics"), ("Sidharth", "V.", "Physics"), ("Lekshmi", "Nair", "Physics"), ("Rajesh", "M.", "Physics"),
            ("Fathima", "Beevi", "Chemistry"), ("Reshma", "K.", "Chemistry"), ("Bindu", "Madhavan", "Chemistry"), ("Sajith", "Raghav", "Chemistry"), ("Neethu", "S.", "Chemistry"),
            ("Mohandas", "Nair", "Mathematics"), ("Latha", "Mahesh", "Mathematics"), ("Suresh", "Pillai", "Mathematics"), ("Jayan", "K.", "Mathematics"), ("Asha", "Gopinath", "Mathematics"),
            ("Gopika", "Parameshwaran", "Accountancy"), ("K.P.", "Narayanan", "Accountancy"), ("Aswathy", "Menon", "Business Studies"), ("Siddharth", "Pillai", "Business Studies"),
            ("Philipose", "Marar", "History"), ("Sarah", "Joseph", "History"), ("K.R.", "Gowri", "Political Science"), ("P.J.", "Joseph", "Political Science"), ("Rema", "Devi", "Sociology"), ("Manju", "Warrier", "Sociology"),
            ("Varghese", "Mathew", "Economics"), ("Sreejith", "K.V.", "Economics"), ("Radhika", "Nair", "Economics"),
            ("Sumi", "Santosh", "Home Science")
        ]

        with transaction.atomic():
            self.stdout.write(self.style.WARNING("Wiping Staff, Allocation, and old User data..."))
            SubjectAllocation.objects.all().delete()
            Staff.objects.all().delete()
            
            # THE MAGIC BULLET: Destroy all non-admin users to break the 'Student' curse
            User.objects.filter(is_superuser=False).delete()

            teacher_group, _ = Group.objects.get_or_create(name='Teacher')
            classrooms = ClassRoom.objects.filter(standard__in=[11, 12])
            
            all_required_subjects = set()
            for subjects in STREAM_MAPPING.values():
                all_required_subjects.update(subjects)
            for sub_name in all_required_subjects:
                Subject.objects.get_or_create(name=sub_name)
            
            hindi_split_sub, _ = Subject.objects.get_or_create(name="Hindi (Secondary)")

            self.stdout.write(self.style.SUCCESS(f"Creating 50 fresh, clean Teacher profiles..."))

            for count, (first, last, sub_name) in enumerate(faculty_pool):
                username = f"{first.lower()}_{last.lower().replace('.', '').replace(' ', '')}"
                
                # Create the User entirely fresh
                user, created = User.objects.get_or_create(
                    username=username, 
                    defaults={
                        'first_name': first, 
                        'last_name': last, 
                    }
                )
                
                user.is_staff = True  
                user.is_superuser = False
                user.set_password("kerala@123")
                user.save()

                # Lock in the Teacher group cleanly
                user.groups.set([teacher_group]) 

                dept, _ = Department.objects.get_or_create(name=sub_name)
                
                Staff.objects.create(
                    user=user, 
                    staff_id=f"TCH-2026-{count+1:03d}", 
                    department=dept,
                    designation=f"HSST {sub_name}", 
                    qualification=f"PG with B.Ed in {sub_name}",
                    status='Active', 
                    is_teaching_staff=True
                )

            for classroom in classrooms:
                stream_name = classroom.stream.name if classroom.stream else None
                if stream_name in STREAM_MAPPING:
                    for subject_name in STREAM_MAPPING[stream_name]:
                        target_subject = Subject.objects.get(name=subject_name)

                        if subject_name == 'Malayalam/Hindi':
                            mal_teacher = Staff.objects.filter(department__name="Malayalam").annotate(load=Count('allocations')).order_by('load').first()
                            hin_teacher = Staff.objects.filter(department__name="Hindi").annotate(load=Count('allocations')).order_by('load').first()

                            if mal_teacher:
                                SubjectAllocation.objects.create(staff=mal_teacher, subject=target_subject, classroom=classroom)
                            if hin_teacher:
                                SubjectAllocation.objects.create(staff=hin_teacher, subject=hindi_split_sub, classroom=classroom)
                        
                        else:
                            teacher = Staff.objects.filter(
                                Q(department__name__icontains=subject_name) | Q(designation__icontains=subject_name)
                            ).annotate(current_load=Count('allocations')).order_by('current_load').first()

                            if teacher:
                                SubjectAllocation.objects.create(staff=teacher, subject=target_subject, classroom=classroom)

        self.stdout.write(self.style.SUCCESS("✅ Success: Database sterilized. 50 Teachers built with perfect permissions."))