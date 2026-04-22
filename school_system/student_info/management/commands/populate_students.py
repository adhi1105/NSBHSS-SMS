import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction

from admission.models import ClassRoom
from school_system.models import Subject
from student_info.models import Student 

class Command(BaseCommand):
    help = 'Wipes old students and distributes students with 100% UNIQUE real Kerala names.'

    def handle(self, *args, **kwargs):
        # 1. EXPANDED KERALA NAME POOLS (140 First Names, 40+ Surnames/Initials)
        first_names_m = [
            "Abhinav", "Adithya", "Akhil", "Amal", "Anand", "Arjun", "Ashwin", "Basil", 
            "Cyril", "Dhanush", "Edwin", "Fahad", "Gokul", "Harikrishnan", "Jithin", 
            "Karthik", "Manu", "Nithin", "Pranav", "Rahul", "Roshan", "Sachin", 
            "Sanjay", "Sreejith", "Vaishnav", "Vishnu", "Yadu", "Sidharth", "Praneeth",
            "Abin", "Ajay", "Akash", "Alen", "Anandu", "Anoop", "Aravind", "Asif", 
            "Athul", "Bharath", "Deepak", "Devadath", "Farhaan", "Govind", "Hari", 
            "Jacob", "Joel", "Kiran", "Krishnajith", "Milan", "Mohammed", "Naveen", 
            "Neeraj", "Nihal", "Paul", "Prasanth", "Rizwan", "Rohan", "Rohit", "Sabin", 
            "Salman", "Sanal", "Sarath", "Shafi", "Sooraj", "Sreehari", "Sriram", 
            "Sujith", "Varghese", "Vimal", "Vivek"
        ]
        first_names_f = [
            "Abhirami", "Aiswarya", "Akhila", "Amrutha", "Anagha", "Anjali", "Aparna", 
            "Arya", "Athira", "Devika", "Divya", "Fathima", "Gouri", "Haritha", "Kavya", 
            "Lakshmi", "Malavika", "Meenakshi", "Nandana", "Neha", "Parvathy", "Pooja", 
            "Reshma", "Sandra", "Shilpa", "Sneha", "Sruthi", "Swathi", "Varsha", "Aditi", 
            "Aleena", "Amala", "Ameena", "Ananya", "Aneesha", "Anita", "Anusree", 
            "Archana", "Ashwathy", "Ayisha", "Bhadra", "Bhavana", "Chithra", "Deepa", 
            "Diya", "Farha", "Gayathri", "Gopika", "Hiba", "Irene", "Jesna", "Krishnapriya", 
            "Laya", "Liya", "Meera", "Namitha", "Navya", "Nidhi", "Nithya", "Riya", 
            "Rose", "Safa", "Salma", "Sanika", "Shreya", "Shweta", "Sona", "Surya", 
            "Thara", "Vismaya"
        ]
        surnames = [
            "Nair", "Menon", "Pillai", "Varghese", "Thomas", "Kurian", "Panicker", 
            "Joseph", "Mathew", "George", "Kumar", "Krishnan", "Varma", "Sharma", 
            "Iyer", "Nambiar", "Babu", "Raj", "Rajan", "Mohan", "K.", "S.", "P.", 
            "M.", "R.", "V.", "T.", "A.", "B.", "C.", "D.", "E.", "G.", "H.", "J."
        ]
        house_names = ["Rose Villa", "Green House", "River View", "Sreevalsam", "Padmam", "Kousthubham", "Gokulam", "Karthika"]

        STUDENTS_PER_CLASS = 20

        with transaction.atomic():
            self.stdout.write(self.style.WARNING("Wiping existing Student data..."))
            
            Student.objects.all().delete()
            student_group, _ = Group.objects.get_or_create(name='Student')
            User.objects.filter(groups=student_group).delete()

            classrooms = ClassRoom.objects.all().order_by('standard', 'division')
            
            if not classrooms.exists():
                self.stdout.write(self.style.ERROR("❌ No classrooms found!"))
                return

            eng, _ = Subject.objects.get_or_create(name="English")
            mal, _ = Subject.objects.get_or_create(name="Malayalam")
            hin, _ = Subject.objects.get_or_create(name="Hindi")

            total_generated = 0
            student_counter = 1
            
            # Tracking set to guarantee absolute name uniqueness
            used_names = set()

            self.stdout.write(self.style.SUCCESS(f"Distributing {STUDENTS_PER_CLASS} unique students to each class..."))

            for classroom in classrooms:
                for roll_no in range(1, STUDENTS_PER_CLASS + 1):
                    
                    # --- UNIQUE NAME GENERATOR ---
                    while True:
                        is_male = random.choice([True, False])
                        first = random.choice(first_names_m) if is_male else random.choice(first_names_f)
                        last = random.choice(surnames)
                        full_name = f"{first} {last}"
                        
                        # Only break the loop if this exact name combo hasn't been used yet
                        if full_name not in used_names:
                            used_names.add(full_name)
                            break
                    
                    # Generate a perfectly unique student ID and matching username
                    student_id_str = f"STU2026{student_counter:03d}"
                    username = student_id_str.lower()

                    # 1. Create User
                    user = User.objects.create_user(
                        username=username,
                        password='123',
                        first_name=first,
                        last_name=last,
                        is_staff=False, 
                        is_superuser=False
                    )

                    # 2. Nuclear Role Lock
                    user.groups.set([student_group])

                    dob = date(2009, 1, 1) + timedelta(days=random.randint(0, 365))

                    # 3. Create Student Profile
                    Student.objects.create(
                        user=user,
                        student_id=student_id_str, 
                        classroom=classroom,
                        roll_number=roll_no,
                        stream=classroom.stream, 
                        first_language=eng,
                        second_language=random.choice([mal, hin]),
                        status='pursuing', 
                        is_active=True,
                        date_of_birth=dob,
                        gender='M' if is_male else 'F',
                        father_name=f"{random.choice(first_names_m)} {last}",
                        address=f"{random.choice(house_names)}, Thazhakara, Kerala, India"
                    )
                    
                    student_counter += 1
                    total_generated += 1

                self.stdout.write(f"Populated {classroom.standard}-{classroom.division} with unique names.")

        self.stdout.write(self.style.SUCCESS(f"✅ Success: {total_generated} Unique Kerala students created. All logins set to '123'."))