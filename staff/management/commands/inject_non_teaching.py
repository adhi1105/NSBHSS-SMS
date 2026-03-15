from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from staff.models import Staff, Department

class Command(BaseCommand):
    help = 'Injects dummy non-teaching staff nodes into the registry and syncs profiles.'

    def handle(self, *args, **kwargs):
        # 1. Ensure an Administrative Department exists
        admin_dept, _ = Department.objects.get_or_create(name='Administration')

        # 2. The Identity Matrix: Authentic Kerala Names
        staff_nodes = [
            {
                'username': 'cashier_anandu', 
                'password': 'Eduplex@Anandu', 
                'email': 'anandu.nair@eduplex.local',
                'first_name': 'Anandu', 
                'last_name': 'Nair',
                'role': 'Cashier',
                'designation': 'Financial Officer',
                'staff_id': 'NT-001'
            },
            {
                'username': 'dept_lakshmi', 
                'password': 'Eduplex@Lakshmi', 
                'email': 'lakshmi.menon@eduplex.local',
                'first_name': 'Lakshmi', 
                'last_name': 'Menon',
                'role': 'Dept_Admin', 
                'designation': 'Department Administrator',
                'staff_id': 'NT-002'
            },
            {
                'username': 'lib_george', 
                'password': 'Eduplex@George', 
                'email': 'george.kurian@eduplex.local',
                'first_name': 'George', 
                'last_name': 'Kurian',
                'role': 'Librarian',
                'designation': 'Chief Librarian',
                'staff_id': 'NT-003'
            },
            {
                'username': 'office_fathima', 
                'password': 'Eduplex@Fathima', 
                'email': 'fathima.m@eduplex.local',
                'first_name': 'Fathima', 
                'last_name': 'Mohammed',
                'role': 'Office_Staff',
                'designation': 'Front Desk Operations',
                'staff_id': 'NT-004'
            }
        ]

        self.stdout.write(self.style.WARNING('\n--- INITIALIZING KERALA STAFF NODES ---'))

        for node in staff_nodes:
            # 1. Inject or Update the Base User Identity
            user, u_created = User.objects.get_or_create(username=node['username'])
            user.email = node['email']
            user.first_name = node['first_name']
            user.last_name = node['last_name']
            user.set_password(node['password'])
            user.save()

            # 2. Inject or Update the Staff Profile
            staff_profile, s_created = Staff.objects.get_or_create(user=user)
            staff_profile.staff_id = node['staff_id']
            staff_profile.designation = node['designation']
            staff_profile.department = admin_dept
            staff_profile.role = node['role']
            staff_profile.is_teaching_staff = False
            
            # THE MAGIC HAPPENS HERE:
            # Calling .save() on the Staff model triggers our post_save signal!
            # The signal will automatically force user.is_staff=True and assign the correct Group.
            staff_profile.save() 
            
            status = "CREATED" if u_created else "UPDATED"
            self.stdout.write(
                self.style.SUCCESS(f"[{status}] {user.first_name} {user.last_name} | Mapped to Role: {node['role']}")
            )

        self.stdout.write(self.style.WARNING('--- PROVISIONING COMPLETE ---\n'))