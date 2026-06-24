import stripe
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
from courses.models import Course, SignUp
from students.models import Student
from datetime import datetime
from django.utils import timezone
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

def stripe_value_id(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.get("id", "")

def money_to_stripe_amount(amount):

    decimal_amount = Decimal(str(amount))
    
    stripe_amount = (decimal_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    
    return int(stripe_amount)

def stripe_object_value(obj, key, default=None):
    if hasattr(obj, "get"):
        return obj.get(key, default)
    return getattr(obj, key, default)


def create_signup_from_checkout_session(session):
    
    metadata = stripe_object_value(session, "metadata", {}) or {}

    course_id = stripe_object_value(metadata, "course_id")
    student_id = stripe_object_value(metadata, "student_id")
    session_id = stripe_object_value(session, "id")

    if not course_id or not student_id or not session_id:
        raise ValueError("Stripe Checkout Session is missing course_id or student_id metadata.")

    with transaction.atomic():
        course = Course.objects.select_for_update().get(id=course_id)
        student = Student.objects.get(id=student_id)

        existing_signup = SignUp.objects.filter(online_payment_session=session_id).first()
        if existing_signup:
            return existing_signup, False
        
        existing_paid_signup = SignUp.objects.filter(
            course=course,
            student=student,
            sign_up_status="success",
            payment_date__isnull=False,
            cancel_date__isnull=True,
        ).first()
        if existing_paid_signup:
            return existing_paid_signup, False

        # ==========================================
        # 新增區塊：終極名額判定
        # ==========================================
        current_count = SignUp.objects.filter(
            course=course,
            sign_up_status="success", #only count success
            cancel_date__isnull=True
        ).exclude(file_status="deleted").count()

        if current_count < course.max_no_student:
            final_status = "success"
        else:
            final_status = "waiting_list" #名額滿了，判定為超賣候補
            print(f"警告：課程 {course.name} 發生超賣！學生 ID: {student.id} 已付款但被列入候補名單。")
            #超賣 action, maybe send email?

            #
        # ==========================================

        current_datetime = timezone.localtime(timezone.now())
        payment_method = ""
        payment_method_types = stripe_object_value(session, "payment_method_types", []) or []
        if payment_method_types:
            payment_method = payment_method_types[0]

        payment_intent = stripe_value_id(stripe_object_value(session, "payment_intent"))
        amount_total = stripe_object_value(session, "amount_total", 0) or 0
        created_timestamp = stripe_object_value(session, "created")
        payment_date = current_datetime
        if created_timestamp:
            payment_date = datetime.fromtimestamp(created_timestamp, tz=timezone.get_current_timezone())

        signup = SignUp.objects.create(
            student=student,
            course=course,
            sign_up_status=final_status,
            sign_up_date=current_datetime,
            payment_date=payment_date,
            payment_amount=Decimal(amount_total) / Decimal("100"),
            payment_method=payment_method or "Stripe",
            payment_ref=payment_intent,
            online_payment_session=session_id,
            payment_remarks="",
            created_by=f"student_id:{student.id}",
            last_updated_by=f"student_id:{student.id}",
        )
        return signup, True