from django.contrib.auth.models import User, Group
from django.db import transaction
from student_info.models import Student
from admission.models import ClassRoom
from exam.models import MarkSheet

def force_sync_stuck_staff():
    """
    Specifically targets the 41 stuck teachers and forces 
    them into the Teacher group.
    """
    stuck_list = [
        'p.j._joseph', 'k.r._gowri', 'sarah_joseph', 'philipose_marar', 
        'siddharth_pillai', 'aswathy_menon', 'k.p._narayanan', 
        'gopika_parameshwaran', 'asha_gopinath', 'jayan_k', 'suresh_pillai', 
        'latha_mahesh', 'mohandas_nair', 'neethu_s', 'sajith_raghav', 
        'bindu_madhavan', 'reshma_k', 'fathima_beevi', 'rajesh_m', 
        'lekshmi_nair', 'jacob_punnoose', 'kurien_thomas', 'sneha_prakash', 
        'arjun_das', 'mathew_scaria', 'deepa_panicker', 'meera_sankar', 
        'raji_viswanath', 'suresh_kumarv', 'maya_ramesh', 'vishnu_prasad', 
        'remya_krishnan', 'pradeep_kumar', 'nandini_varma', 'sreedevi_amma', 
        'gautham_krishna', 'saritha_vinod', 'deepak_nair', 'preethi_chandran', 
        'biju_balakrishnan', 'anjali_menon'
    ]

    teacher_group, _ = Group.objects.get_or_create(name='Teacher')
    fixed_count = 0

    # We use filter to avoid 'DoesNotExist' errors if a user was deleted
    users = User.objects.filter(username__in=stuck_list)
    
    for user in users:
        user.is_staff = True
        user.groups.set([teacher_group]) # Destructive sync
        user.save()
        fixed_count += 1
        
    return fixed_count

def promote_grade_11_to_12(source_classroom_id, target_classroom_id, pass_mark=35):
    """
    Registry Operation: Batch promotes students who met the passing criteria.
    """
    source_class = ClassRoom.objects.get(id=source_classroom_id)
    target_class = ClassRoom.objects.get(id=target_classroom_id)
    
    # Identify students currently in the source classroom
    eligible_students = Student.objects.filter(classroom=source_class, is_active=True)
    
    promoted_count = 0
    failed_count = 0

    with transaction.atomic():
        for student in eligible_students:
            # Check for failing grades in any core subject
            has_failed = MarkSheet.objects.filter(
                student=student, 
                marks_obtained__lt=pass_mark,
                exam__exam_type='Final'
            ).exists()

            if not has_failed:
                # MIGRATE NODE: Move to Grade 12
                student.classroom = target_class
                # Update any other session-specific flags
                student.save()
                promoted_count += 1
            else:
                failed_count += 1
                
    return promoted_count, failed_count