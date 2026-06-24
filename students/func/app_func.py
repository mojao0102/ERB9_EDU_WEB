import secrets
from ..models import Student

def generate_unique_student_number():
    while 1:
        random_digits = secrets.randbelow(900000) + 100000
        temp_student_no = f"STU-{random_digits}"       
        if not Student.objects.filter(student_no=temp_student_no).exists():
            return temp_student_no