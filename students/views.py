# student/views.py
from administration.func import app_func as admin_app_func
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, F, Prefetch
from .models import Student
from .func import app_func as student_app_func
from datetime import datetime
from core.utils import decode_id
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from courses.models import SignUp
from courses.func import app_func as course_app_func
from .forms import StudentForm
from django.utils import timezone
from decimal import Decimal

@admin_app_func.staff_access_control
def student_list(request):
    base_query = Student.objects.order_by('-created_datetime')
    keyword = request.GET.get("txtkeyword", "").strip()
    sort_by = request.GET.get("sort_by", "")
    sort_dir = request.GET.get("sort_dir", "asc")

    filter_active = request.GET.get("filter_active", "")
    if filter_active == "1":
        base_query = base_query.filter(is_active=True)
    elif filter_active == "0":
        base_query = base_query.filter(is_active=False)
    filter_email = request.GET.get("filter_email", "")
    if filter_email == "1":
        base_query = base_query.filter(is_email_verified=True)
    elif filter_email == "0":
        base_query = base_query.filter(is_email_verified=False)

    if keyword:
        base_query = base_query.filter(
            Q(student_no__icontains=keyword)
            | Q(cn_name__icontains=keyword)
            | Q(en_name__icontains=keyword)
            | Q(contact1_phone__icontains=keyword)
        )

    sort_allow = ["student_no", "cn_name", "en_name", "dob", "contact1_name", "contact1_phone", "is_active", "is_email_verified"]
    if sort_by in sort_allow:
        order_field = sort_by if sort_dir == "asc" else f"-{sort_by}"
        students = base_query.order_by(order_field)
    else:
        students = base_query

    paginator = Paginator(students, 15) 
    page_number = request.GET.get('page', 1)   
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    input_data = {
        "txtkeyword": keyword,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "filter_active": filter_active,  # 回傳前端保持選項狀態
        "filter_email": filter_email,}
    context = {"page_obj": page_obj, "input_data": input_data}
    return render(request, "students/student_list.html", context)

@admin_app_func.staff_access_control
def student_edit(request, hash_student=None):

    if hash_student:
        if not (student_id := decode_id(hash_student)):
            raise Http404("無效的學生")  
        student = get_object_or_404(Student, Q(id=student_id) & ~Q(file_status='deleted'))
    else:
        student = None

    if request.method == 'POST':

        print(f"view: {request.POST.get('is_active')}")

        form = StudentForm(request.POST, instance=student)       
        if form.is_valid():
            obj_student = form.save(commit=False)

            obj_student.last_updated_by = request.obj_staff.username
            obj_student.created_by = obj_student.created_by if student else request.obj_staff.username

            obj_student.register_date = obj_student.register_date if student else timezone.now()
            obj_student.is_email_verified = obj_student.is_email_verified if student else True
            obj_student.student_no = obj_student.student_no if student else student_app_func.generate_unique_student_number()
            obj_student.is_active = True if request.POST.get('is_active') else False

            str_success_message = '學生資訊已更新' if student else '成功建立學生記錄'
            str_error_message = '更新學生失敗，請聯絡系統管理員' if student else '建立學生記錄失敗，請聯絡系統管理員'

            try:
                obj_student.save()
                messages.success(request, str_success_message)      
                return redirect('students:student_list')
            except Exception as e:
                print(f"Error: {str(e)}")
                messages.error(request, str_error_message)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:#GET
        form = StudentForm(instance=student)
    return render(request, "students/student_edit.html", {'form': form, 'student': student})

@admin_app_func.staff_access_control
def student_delete(request, hash_student):
    if not (student_id := decode_id(hash_student)):
        raise Http404("無效的學生")  
    obj_student = get_object_or_404(Student, Q(id=student_id) & ~Q(file_status='deleted'))

    #Check if any transactions
    if (list_trans := course_app_func.get_transaction_list(**{'student_id': obj_student.id})):
        messages.error(request, "該學生在系統中已有交易記錄，您的刪除要求已被拒絕，請考慮停用該學生記錄")
    else:
        try:
            obj_student.delete()
            messages.success(request, "成功刪除學生記錄")
            return redirect('students:student_list')
        except Exception as e:
            print(f"刪除學生失敗: {str(e)}")
            messages.error(request, "刪除學生記錄失敗，請聯絡系統管理員")
    return redirect('students:student_edit', hash_student)


@admin_app_func.staff_access_control
def student_view(request, hash_student):

    student_id = decode_id(hash_student)
    if not student_id:
        raise Http404("無效的學生")  

    student = get_object_or_404(Student, id=student_id)

    list_courses = course_app_func.get_courses_with_dynamic_status(signup__student_id=student_id)\
    .exclude(signup__file_status="deleted")\
    .annotate(sign_up_date=F('signup__sign_up_date'), sign_up_status=F('signup__sign_up_status'), cancel_reason=F('signup__cancel_reason'))\
    .select_related("teacher")\
    .order_by('-signup__sign_up_date').distinct()

    list_trans = course_app_func.get_transaction_list(**{'student_id': student_id}) or []

    total_payment = Decimal('0.00')
    total_refund = Decimal('0.00')
    for trans in list_trans:
        if trans['trans_amount']:
            amount = Decimal(str(trans['trans_amount']))
            if trans['record_type'] == 'payment':
                total_payment += amount
            elif trans['record_type'] == 'refund':
                total_refund += amount
    net_income = total_payment - total_refund

    context = {
        "student": student,
        "list_courses": list_courses,
        "list_trans": list_trans,
        "total_payment": total_payment,
        "total_refund": total_refund,
        "net_income": net_income,
    }
    return render(request, "students/student_view.html", context)