import os
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from administration.models import Center
from django.db.models import Count, Case, When, Value, CharField, F, Q, IntegerField
from django.utils import timezone
from django.contrib import messages
from ..models import Course, SignUp, SignUpRefund, CourseSubCategory, CourseSchedule
from django.utils.dateparse import parse_date, parse_time, parse_datetime
from datetime import timedelta
from core.utils import encode_id
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from datetime import datetime

def generate_payment_receipt_pdf(obj_signup):

    obj_center = Center.objects.first()       
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo', 'logo.png')
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else ""

    context = {'signup': obj_signup, 'student': obj_signup.student, 'center': obj_center, 'logo_url': logo_url,}
    
    html_string = render_to_string('report_template/payment_receipt.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes

def generate_refund_receipt_pdf(obj_refund):

    obj_center = Center.objects.first()
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo', 'logo.png')
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else ""
    print(obj_refund)
    context = {'refund': obj_refund, 'student': obj_refund.sign_up.student, 'center' : obj_center, "logo_url" : logo_url}

    html_string = render_to_string('report_template/refund_receipt.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes

def get_courses_with_dynamic_status(**kwargs):
    current_time = timezone.now()
    keyword = kwargs.pop('keyword', None)
    list_course = Course.objects.exclude(file_status="deleted").order_by("-created_datetime")

    if keyword:
        keyword = keyword.strip()
        list_course = list_course.filter(
            Q(name__icontains=keyword) | 
            Q(code__icontains=keyword) | 
            Q(teacher__title__icontains=keyword) | 
            Q(teacher__first_name__icontains=keyword) |
            Q(teacher__last_name__icontains=keyword))
        
    if kwargs:
        list_course = list_course.filter(**kwargs)

    valid_signup_condition = (
        Q(signup__payment_date__isnull=False) &
        Q(signup__sign_up_status="success") & 
        Q(signup__cancel_date__isnull=True) & 
        ~Q(signup__file_status="deleted"))   
    cancelled_signup_condition = (
        Q(signup__payment_date__isnull=False) &
        Q(signup__sign_up_status="cancel") & 
        Q(signup__cancel_date__isnull=False) & 
        ~Q(signup__file_status="deleted"))  
    refund_record_condition = (
        ~Q(signup__signuprefund__file_status="deleted") &
        Q(signup__signuprefund__id__isnull=False) &
        Q(signup__signuprefund__refund_amount__isnull=False) &
        Q(signup__signuprefund__refund_date__isnull=False) &
        ~Q(signup__file_status="deleted")
    )
    
    list_course = list_course.annotate(   
        current_signup_count=Count('signup', filter=valid_signup_condition, distinct=True),
        cancelled_signup_count=Count('signup', filter=cancelled_signup_condition, distinct=True),
        refund_record_count=Count('signup__signuprefund', filter=refund_record_condition, distinct=True),
        course_dynamic_status=Case(
            When(course_status='cancel', then=Value('已取消')),
            When(Q(period_to__lt=current_time.date()) | Q(period_to=current_time.date(), time_to__lt=current_time.time()), 
            then=Value('已完結')),
            When(Q(period_from__lt=current_time.date()) | Q(period_from=current_time.date(), time_from__lte=current_time.time()), 
            then=Value('進行中')),
            When(registation_expiry_date__lt=current_time, then=Value('截止報名')),
            When(current_signup_count__gte=F('max_no_student'), then=Value('人數已滿')),
            default=Value('報名中'),output_field=CharField()),)
    return list_course

def course_set_publish(request, list_course_id):
    try:
        temp_course = Course.objects.filter(id__in=list_course_id).update(is_web_publish=True, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course set web publish fail: {e}")
        return False
    
def course_undo_publish(request, list_course_id):
    try:
        temp_course = Course.objects.filter(id__in=list_course_id).update(is_web_publish=False, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course undo web publish fail: {e}")
        return False 

def course_set_promote(request, list_course_id):
    try:
        temp_course = Course.objects.filter(id__in=list_course_id).update(is_promote=True, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course set web promote fail: {e}")
        return False
    
def course_undo_promote(request, list_course_id):
    try:
        temp_course = Course.objects.filter(id__in=list_course_id).update(is_promote=False, last_updated_by=request.obj_staff.username)
        return True
    except Exception as e:
        print(f"Course undo web promote fail: {e}")
        return False 
    
def validate_and_parse_course_form(request):
    #Return Tuple: (is_valid: bool, parsed_data: dict)
    is_valid = True
    parsed_data = request.POST.dict() 

    if not request.POST.get("name", "").strip():
        messages.error(request, "課程名稱為必填欄位")
        is_valid = False

    if not (sub_category_id := request.POST.get("sub_category_id", "").strip()):
        messages.error(request, "請選擇課程類別")
        is_valid = False
        parsed_data["sub_category_id"] = None
    else:
        parsed_data["sub_category_id"] = int(sub_category_id)

    if not (teacher_id := request.POST.get("teacher_id", "").strip()):
        messages.error(request, "請選擇負責導師")
        is_valid = False
        parsed_data["teacher_id"] = None
    else:
        parsed_data["teacher_id"] = int(teacher_id)

    parsed_data["room_id"] = int(request.POST.get("room_id")) if request.POST.get("room_id") and request.POST.get("room_id").isdigit() else None

    course_fee = request.POST.get("course_fee", "").strip()
    if not course_fee:
        messages.error(request, "請填寫課程費用")
        is_valid = False
    else:
        try:
            if float(course_fee) <= 0:
                messages.error(request, "課程費用必須大於 0")
                is_valid = False
        except ValueError:
            messages.error(request, "課程費用格式錯誤，必須是數字")
            is_valid = False

    total_lessons = request.POST.get("total_lessons", "").strip()
    if not total_lessons or not total_lessons.isdigit() or int(total_lessons) <= 0:
        messages.error(request, "總堂數必須是大於 0 的整數")
        is_valid = False

    max_no_student = request.POST.get("max_no_student", "").strip()
    if not max_no_student or not max_no_student.isdigit() or int(max_no_student) <= 0:
        messages.error(request, "人數上限必須是大於 0 的整數")
        is_valid = False

    if not (registation_expiry_date:=parse_datetime(request.POST.get("registation_expiry_date", '').strip())) or not (period_from:=parse_date(request.POST.get("period_from", '').strip())) or not (period_to:=parse_date(request.POST.get("period_to", '').strip())):
        messages.error(request, "請輸入有效的日期與時間格式")
        is_valid = False
    else:
        if timezone.is_naive(registation_expiry_date):
            registation_expiry_date = timezone.make_aware(registation_expiry_date)
        if registation_expiry_date.date() >= period_from:
            messages.error(request, "報名截止日期不能晚於課程開始日期")
            is_valid = False
        if period_from > period_to:
            messages.error(request, "課程結束日期必須 >= 課程開始日期")
            is_valid = False           
    parsed_data["registation_expiry_date"] = registation_expiry_date or None
    parsed_data["period_from"] = period_from or None
    parsed_data["period_to"] = period_to or None

    if not (time_from:= parse_time(request.POST.get("time_from", '').strip())) or not (time_to:= parse_time(request.POST.get("time_to", '').strip())):
        messages.error(request, "請填寫有效的上課時間")
        is_valid = False
    else:
        if time_from >= time_to:
            messages.error(request, "上課結束時間必須 > 上課開始時間")
            is_valid = False
    parsed_data["time_from"] = time_from
    parsed_data["time_to"] = time_to

    parsed_data["is_web_publish"] = request.POST.get("is_web_publish") == "on"
    parsed_data["is_promote"] = request.POST.get("is_promote") == "on"
    
    for i in range(1, 9):
        parsed_data[f"feature_{i}"] = request.POST.get(f"feature_{i}", "").strip()

    parsed_data["age_group"] = request.POST.get("age_group", "").strip()
    print(parsed_data["age_group"])
    selected_weekdays = request.POST.getlist("lesson_weekdays")
    parsed_data["is_mon"] = '1' in selected_weekdays
    parsed_data["is_tue"] = '2' in selected_weekdays
    parsed_data["is_wed"] = '3' in selected_weekdays
    parsed_data["is_thu"] = '4' in selected_weekdays
    parsed_data["is_fri"] = '5' in selected_weekdays
    parsed_data["is_sat"] = '6' in selected_weekdays
    parsed_data["is_sun"] = '7' in selected_weekdays

    total_lessons = request.POST.get("total_lessons", "").strip()
    if total_lessons and total_lessons.isdigit():
        if len(selected_weekdays) > int(total_lessons):
            messages.error(request, "每週勾選的上課天數不能超過課程總堂數")
            is_valid = False

    if is_valid and period_from and period_to and total_lessons and total_lessons.isdigit():
        available_days = 0
        current_date = period_from
        
        while current_date <= period_to:
            # isoweekday() returns weekday(1 - 7)
            if str(current_date.isoweekday()) in selected_weekdays:
                available_days += 1
            current_date += timedelta(days=1)
            
        if available_days < int(total_lessons):
            messages.error(request, f"日期區間錯誤！從 {period_from} 到 {period_to} 只有 {available_days} 天符合你勾選的星期，無法排滿 {total_lessons} 堂課！")
            is_valid = False

    return is_valid, parsed_data

def get_transaction_list(**kwargs):
    # Set Empty List
    payment_list = None
    refund_list = None

    # Get filter
    record_type = kwargs.get('record_type')
    student_id = kwargs.get('student_id')
    course_id = kwargs.get('course_id')
    date_from = kwargs.get('date_from')
    date_to = kwargs.get('date_to')
    trans_method =  kwargs.get('trans_method')
    main_category_id = kwargs.get('main_category_id')
    sub_category_id = kwargs.get('sub_category_id')
    keyword = kwargs.get('keyword')

    if not record_type or record_type == 'payment':
        payment_list = SignUp.objects.exclude(payment_date__isnull=True, file_status="deleted").select_related('student')    
        payment_list = payment_list.filter(student_id=student_id) if student_id else payment_list
        payment_list = payment_list.filter(course_id=course_id) if course_id else payment_list
        payment_list = payment_list.filter(payment_date__gte=date_from) if date_from else payment_list
        payment_list = payment_list.filter(payment_date__lte=date_to) if date_to else payment_list
        payment_list = payment_list.filter(payment_method=trans_method) if trans_method else payment_list
        payment_list = payment_list.filter(course__sub_category__main_category_id=main_category_id) if main_category_id else payment_list
        payment_list = payment_list.filter(course__sub_category_id=sub_category_id) if sub_category_id else payment_list
        
        if keyword :
            payment_list = payment_list.filter(
                Q(student__cn_name__icontains=keyword) |
                Q(student__en_name__icontains=keyword) |
                Q(student__student_no__icontains=keyword) |
                Q(course__name__icontains=keyword) |
                Q(payment_ref__icontains=keyword)
            )
            
        payment_list = payment_list.annotate(
            record_type=Value('payment', output_field=CharField()),
            sign_up_id=F('id'),
            refund_id=Value(0, output_field=IntegerField()),
            signup_status=F('sign_up_status'),
            reason=F('cancel_reason'),
            student_cn=F('student__cn_name'),
            student_en=F('student__en_name'),
            student_no=F('student__student_no'),
            course_name=F('course__name'),
            course_code=F('course__code'),
            main_category_id=F('course__sub_category__main_category_id'), 
            sub_category_id=F('course__sub_category_id'),     
            main_category_short=F('course__sub_category__main_category__short_name'),
            sub_category_name=F('course__sub_category__name'),
            trans_date=F('payment_date'),
            trans_amount=F('payment_amount'),
            trans_method=F('payment_method'),
            trans_ref=F('payment_ref'),
            trans_status=F('sign_up_status')
        ).values(
            'record_type', 'course_id', 'sign_up_id', 'refund_id', 'signup_status', 'reason', 'student_id',
            'student_cn', 'student_en', 'student_no', 'course_name', 'course_code',
            'main_category_id', 'sub_category_id',
            'main_category_short', 'sub_category_name',
            'trans_date', 'trans_amount', 'trans_method', 'trans_ref', 'online_payment_session', 'trans_status'
        )
            
    if not record_type or record_type == 'refund':
        refund_list = SignUpRefund.objects.exclude(refund_date__isnull=True, file_status="deleted").select_related('sign_up__student')
        
        refund_list = refund_list.filter(sign_up__student_id=student_id) if student_id else refund_list
        refund_list = refund_list.filter(sign_up__course_id=course_id) if course_id else refund_list
        refund_list = refund_list.filter(refund_date__gte=date_from) if date_from else refund_list
        refund_list = refund_list.filter(refund_date__lte=date_to) if date_to else refund_list
        refund_list = refund_list.filter(refund_method=trans_method) if trans_method else refund_list
        refund_list = refund_list.filter(sign_up__course__sub_category__main_category_id=main_category_id) if main_category_id else refund_list
        refund_list = refund_list.filter(sign_up__course__sub_category_id=sub_category_id) if sub_category_id else refund_list

        if keyword:
            refund_list = refund_list.filter(
                Q(sign_up__student__cn_name__icontains=keyword) |
                Q(sign_up__student__en_name__icontains=keyword) |
                Q(sign_up__student__student_no__icontains=keyword) |
                Q(sign_up__course__name__icontains=keyword) |
                Q(refund_ref__icontains=keyword)
            )

        refund_list = refund_list.annotate(
            record_type=Value('refund', output_field=CharField()),
            course_id=F('sign_up__course_id'),
            refund_id=F('id'),
            signup_status=F('sign_up__sign_up_status'),
            reason=F('refund_reason'),
            student_id=F('sign_up__student__id'),
            student_cn=F('sign_up__student__cn_name'),
            student_en=F('sign_up__student__en_name'),
            student_no=F('sign_up__student__student_no'),
            course_name=F('sign_up__course__name'),
            course_code=F('sign_up__course__code'),
            main_category_id=F('sign_up__course__sub_category__main_category_id'),
            sub_category_id=F('sign_up__course__sub_category_id'),       
            main_category_short=F('sign_up__course__sub_category__main_category__short_name'),
            sub_category_name=F('sign_up__course__sub_category__name'),
            trans_date=F('refund_date'),
            trans_amount=F('refund_amount'),
            trans_method=F('refund_method'),
            trans_ref=F('refund_ref'),
            online_payment_session=Value('', output_field=CharField()),
            trans_status=Value('refunded', output_field=CharField())
        ).values(
            'record_type', 'course_id', 'sign_up_id', 'refund_id', 'signup_status', 'reason', 'student_id',
            'student_cn', 'student_en', 'student_no', 'course_name', 'course_code',
            'main_category_id', 'sub_category_id',
            'main_category_short', 'sub_category_name',
            'trans_date', 'trans_amount', 'trans_method', 'trans_ref', 'online_payment_session', 'trans_status'
        )

    if payment_list is not None and refund_list is not None:
        list_trans = payment_list.union(refund_list).order_by("-trans_date")
    elif payment_list is not None:
        list_trans = payment_list.order_by("-trans_date")
    elif refund_list is not None:
        list_trans = refund_list.order_by("-trans_date")
    else:
        return []
    
    list_processed_trans = []
    for dict_trans in list_trans:
        dict_trans['sign_up_id'] = encode_id(dict_trans['sign_up_id']) 
        dict_trans['refund_id'] = encode_id(dict_trans['refund_id']) if dict_trans['refund_id'] else ""
        dict_trans['student_id'] = encode_id(dict_trans['student_id'])
        dict_trans['course_id'] = encode_id(dict_trans['course_id'])
        list_processed_trans.append(dict_trans)
        
    return list_processed_trans

def cancel_signup(obj_staff, **kwargs):
    course_id = kwargs.get('course_id')
    signup_id = kwargs.get('signup_id')
    reason = kwargs.get('cancel_reason')

    if not course_id or not signup_id:
        raise ValueError("課程或報名ID不存在")
    if not reason:
        raise ValueError("取消原因不存在")
        
    try:
        with transaction.atomic():
            list_signup = SignUp.objects.exclude(file_status="deleted").exclude(sign_up_status='cancel')

            if course_id:
                list_signup = list_signup.filter(course_id=course_id)
                
            if signup_id:
                list_signup = list_signup.filter(id=signup_id)

            signups_to_notify = list(list_signup.select_related('student', 'course'))

            updated_count = list_signup.update(
                sign_up_status='cancel', 
                cancel_date=timezone.now(), 
                cancel_by=obj_staff, 
                cancel_reason=reason, 
                last_updated_by=obj_staff.username)
            
            obj_center = Center.objects.first()
            target_url = "http://127.0.0.1:8000/dashboard/" 
            
            for signup in signups_to_notify:
                if signup.student.email:
                    context = {
                        'student': signup.student,
                        'course': signup.course,
                        'cancel_reason': reason,
                        'cancel_date': timezone.now(),
                        'center': obj_center,
                        'target_url': target_url}
                    send_async_email(
                        subject=f"【{obj_center.name}】課程報名取消通知 - {signup.course.name}",
                        template_name="email_templates/cancel_email.html",
                        context=context,
                        recipient_list=[signup.student.email])
                
            return updated_count
    except ValueError as e:
        raise e
    except Exception as e:
        print(f"取消課程失敗: {str(e)}")
        raise Exception("系統在處理連動取消時發生資料庫異常。")

def refund_signup(obj_staff, **kwargs):
    signup_id = kwargs.get('signup_id')
    refund_reason = kwargs.get('refund_reason')
    refund_method = kwargs.get('refund_method')
    refund_amount = kwargs.get('refund_amount')
    refund_ref = kwargs.get('refund_ref')

    if not signup_id: raise ValueError("報名ID不存在")
    if not refund_reason: raise ValueError("退款原因不存在")
    if not refund_method: raise ValueError("退款方式不存在")
    if not refund_amount: raise ValueError("退款金額不存在")
    if not refund_ref: raise ValueError("退款參考編號不存在")

    try:
        refund_amount = Decimal(str(refund_amount).strip())
        if refund_amount <= 0:
            raise ValueError("退款金額必須大於0")
    except InvalidOperation:
        raise ValueError("退款金額格式錯誤")

    try:
        with transaction.atomic():
            obj_signup = SignUp.objects.select_for_update().filter(id=signup_id).exclude(file_status="deleted").first()
            if not obj_signup:
                raise ValueError("報名記錄不存在")

            refunded_total = SignUpRefund.objects.filter(sign_up_id=signup_id).exclude(file_status='deleted').aggregate(total=Sum('refund_amount', default=0))["total"]
            if obj_signup.payment_amount < (refunded_total + refund_amount):
                available = obj_signup.payment_amount - refunded_total
                raise ValueError(f"退款總額 (${refunded_total + refund_amount}) 大於原始付款金額！該訂單目前最多僅能再退款 ${available}。")
            
            new_refund = SignUpRefund.objects.create(
                sign_up=obj_signup,
                refund_date=timezone.now(),
                refund_method=refund_method,
                refund_amount=refund_amount,
                refund_ref=refund_ref,
                refund_by=obj_staff,  
                refund_reason=refund_reason,
                last_updated_by=obj_staff.username)
            
            # Email
            if obj_signup.student.email:
                obj_center = Center.objects.first()
                target_url = "http://127.0.0.1:8000/dashboard/"
                context = {
                    'student': obj_signup.student,
                    'course': obj_signup.course,
                    'refund': new_refund,
                    'center': obj_center,
                    'target_url': target_url}            
                pdf_bytes = generate_refund_receipt_pdf(new_refund)
                file_name = f"Refund_Receipt_{refund_ref}.pdf"
                attachment = (file_name, pdf_bytes, 'application/pdf')
                
                send_async_email(
                    subject=f"【{obj_center.name}】退款處理完成通知 - {obj_signup.course.name}",
                    template_name="email_templates/refund_email.html",
                    context=context,
                    recipient_list=[obj_signup.student.email],
                    attachment=attachment)

            return refund_amount
    except ValueError as e:
        raise e
    except Exception as e:
        print(f"退款建立失敗: {str(e)}")
        raise Exception("資料庫建立退款紀錄時發生未知錯誤。")

def send_async_email(subject, template_name, context, recipient_list, attachment=None):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        
        if attachment:
            file_name, file_content, mime_type = attachment
            msg.attach(file_name, file_content, mime_type)
            
        msg.send()
        print(f"Email 成功發送至: {recipient_list}")
        return True
        
    except Exception as e:
        print(f"Email 發送失敗: {str(e)}")
        return False

def generate_course_code(sub_cate_id):
    try:
        obj_sub_cat = CourseSubCategory.objects.select_related('main_category').get(
            Q(id=sub_cate_id), ~Q(file_status="deleted")
        )
        year_prefix = timezone.now().strftime('%y')
        main_code = obj_sub_cat.main_category.main_cat_code or ""
        sub_code = obj_sub_cat.sub_cat_code or ""
        prefix = f"{year_prefix}{main_code}{sub_code}"

        last_course = Course.objects.filter(
            sub_category=obj_sub_cat
        ).order_by('-id').first()

        next_seq = 1
        
        if last_course and last_course.code and '-' in last_course.code:
            last_seq_str = last_course.code.split('-')[-1]
            if last_seq_str.isdigit():
                next_seq = int(last_seq_str) + 1

        if next_seq > 999:
            print("該類別課程流水號已超過999, 無法產生代碼")
            return ""

        final_course_code = f"{prefix}-{next_seq:03d}"
        return final_course_code

    except CourseSubCategory.DoesNotExist:
        print("找不到對應的子類別")
        return ""
    except Exception as e:
        print(f"Fail: {str(e)}")
        return ""

def save_course_schedule(obj_course, input_date, schedule_id=None, start_time=None, end_time=None, title="", content="", remarks="", staff_username=""):
    
    try:
        #check if input date and is between or equal to period_from and period_to
        target_date = input_date.date() if isinstance(input_date, datetime) else input_date
        if obj_course.period_from and obj_course.period_to:
            if target_date < obj_course.period_from or target_date > obj_course.period_to:
                raise ValueError(f"上課日期 ({target_date}) 必須在課程區間內 ({obj_course.period_from} ~ {obj_course.period_to})")

        final_start = start_time or obj_course.time_from
        final_end = end_time or obj_course.time_to

        
        if schedule_id: #Edit
            try:
                obj_schedule = CourseSchedule.objects.get(id=schedule_id, course=obj_course)
                
                obj_schedule.lesson_date = input_date
                obj_schedule.start_time = final_start
                obj_schedule.end_time = final_end
                obj_schedule.lesson_title = title
                obj_schedule.lesson_content = content
                obj_schedule.remarks = remarks
                obj_schedule.last_updated_by = staff_username
                obj_schedule.save()
                return True
            except CourseSchedule.DoesNotExist:
                raise ValueError("找不到該筆需要編輯的排期資料")

        else:#Create
            existing_count = CourseSchedule.objects.filter(course_id=obj_course.id).exclude(file_status='deleted').exclude(course__file_status='deleted').count()            
            if existing_count >= obj_course.total_lessons:
                raise ValueError(f"此課程的排期堂數（現存 {existing_count} 堂）已達總堂數上限（上限 {obj_course.total_lessons} 堂）。")

            CourseSchedule.objects.create(
                course=obj_course,
                lesson_date=input_date,
                start_time=final_start,
                end_time=final_end,
                lesson_title=title,
                lesson_content=content,
                remarks=remarks,
                created_by=staff_username,
                last_updated_by=staff_username)
            return True

    except ValueError as e:
        raise e
    except Exception as e:
        print(f"Fail to save lesson schedule: {str(e)}")
        raise Exception("資料庫儲存排期時發生未知錯誤。")
