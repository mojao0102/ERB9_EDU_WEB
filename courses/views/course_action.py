from administration.func import app_func as admin_app_func
from ..models import Course, CourseMainCategory, CourseSubCategory, CourseTemplate, SignUp, SignUpRefund, CourseSchedule
from django.http import HttpResponse
from teachers.models import Teacher
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from ..func import app_func as course_app_func
from django.utils.dateparse import parse_date, parse_time
from datetime import datetime, time
from core.utils import decode_id, encode_id
from django.http import Http404
from django.db import transaction
from decimal import Decimal
from django.db.models import Prefetch
from datetime import timedelta
from django.views.decorators.http import require_POST

@admin_app_func.staff_access_control
def download_payment_receipt(request, hash_signup):
    signup_id = decode_id(hash_signup)
    if not signup_id:
        raise Http404("無效的連結")

    obj_signup = get_object_or_404(SignUp, id=signup_id)
    
    pdf_bytes = course_app_func.generate_payment_receipt_pdf(obj_signup)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_signup.payment_ref}.pdf"'  
    return response

@admin_app_func.staff_access_control
def download_refund_receipt(request, hash_refund):
    refund_id = decode_id(hash_refund)
    if not refund_id:
        raise Http404("無效的連結")

    obj_refund = get_object_or_404(SignUpRefund, id=refund_id)
    
    pdf_bytes = course_app_func.generate_refund_receipt_pdf(obj_refund)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_refund.refund_ref}.pdf"'   
    return response

@admin_app_func.staff_access_control
@require_POST
def course_set_publish(request):

    list_id = request.POST.getlist("ceSelectedCourses") 
    if list_id:
        if course_app_func.course_set_publish(request, list_id):
            messages.success(request, f"已成功發佈 {len(list_id)} 門課程")
        else:
            messages.error("課程發佈失敗，請聯絡系統管理員")

    # Pack list filter to url & redirect to it
    query_params = request.POST.copy()
    query_params.pop('ceSelectedCourses', None)
    query_params.pop('csrfmiddlewaretoken', None)     
    base_url = reverse('courses:course_list')
    redirect_url = f"{base_url}?{query_params.urlencode()}" if query_params else base_url 
    return redirect(redirect_url)

@admin_app_func.staff_access_control
@require_POST
def course_undo_publish(request):

    list_id = request.POST.getlist("ceSelectedCourses") 
    if list_id:
        if course_app_func.course_undo_publish(request, list_id):
            messages.success(request, f"已成功撤銷發佈 {len(list_id)} 門課程")
        else:
            messages.error("課程撤銷發佈失敗，請聯絡系統管理員")

    # Pack list filter to url & redirect to it
    query_params = request.POST.copy()
    query_params.pop('ceSelectedCourses', None)
    query_params.pop('csrfmiddlewaretoken', None)     
    base_url = reverse('courses:course_list')
    redirect_url = f"{base_url}?{query_params.urlencode()}" if query_params else base_url 
    return redirect(redirect_url)

@admin_app_func.staff_access_control
@require_POST
def course_set_promote(request):

    list_id = request.POST.getlist("ceSelectedCourses") 
    if list_id:
        if course_app_func.course_set_promote(request, list_id):
            messages.success(request, f"已成功將 {len(list_id)} 門課程設為首頁推廣")
        else:
            messages.error(request, "設定推廣失敗，請聯絡系統管理員")

    # Pack list filter to url & redirect to it
    query_params = request.POST.copy()
    query_params.pop('ceSelectedCourses', None)
    query_params.pop('csrfmiddlewaretoken', None)     
    base_url = reverse('courses:course_list')
    redirect_url = f"{base_url}?{query_params.urlencode()}" if query_params else base_url 
    return redirect(redirect_url)

@admin_app_func.staff_access_control
@require_POST
def course_undo_promote(request):

    list_id = request.POST.getlist("ceSelectedCourses") 
    if list_id:
        if course_app_func.course_undo_promote(request, list_id):
            messages.success(request, f"已成功取消 {len(list_id)} 門課程的首頁推廣")
        else:
            messages.error(request, "取消推廣失敗，請聯絡系統管理員")
            
    # Pack list filter to url & redirect to it
    query_params = request.POST.copy()
    query_params.pop('ceSelectedCourses', None)
    query_params.pop('csrfmiddlewaretoken', None)     
    base_url = reverse('courses:course_list')
    redirect_url = f"{base_url}?{query_params.urlencode()}" if query_params else base_url 
    return redirect(redirect_url)

@admin_app_func.staff_access_control
@require_POST
def course_cancel_signup(request, hash_signup):

    if not (signup_id:= decode_id(hash_signup)):
        messages.error(request, "無法辨識的報名紀錄, 系統已阻擋此操作")
        return redirect('courses:course_list')
    else:
        obj_signup = get_object_or_404(SignUp, Q(id=signup_id) & ~Q(file_status="deleted"))
        hash_course = encode_id(obj_signup.course_id)

        if not (cancel_reason := request.POST.get("cancel_reason", '').strip()):
            messages.error(request, "請填寫取消原因")
        else:
            try:
                course_app_func.cancel_signup(
                    obj_staff=request.obj_staff,
                    course_id=obj_signup.course_id, 
                    signup_id=signup_id,
                    cancel_reason=cancel_reason)
                messages.success(request, "已成功取消該學生的報名")
            except Exception as e:
                messages.error(request, str(e))
        return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=students")

@admin_app_func.staff_access_control
@require_POST
def course_refund_signup(request, hash_signup):

    if not (signup_id:= decode_id(hash_signup)):
        messages.error(request, "無法辨識的報名紀錄, 系統已阻擋此操作")
        return redirect('courses:course_list')
    else:
        obj_signup = get_object_or_404(SignUp, Q(id=signup_id) & ~Q(file_status="deleted"))
        hash_course = encode_id(obj_signup.course_id)

        try:
            course_app_func.refund_signup(
                obj_staff=request.obj_staff,
                signup_id=signup_id,
                refund_reason=request.POST.get("refund_reason", "").strip(),
                refund_method=request.POST.get("refund_method", "").strip(),
                refund_amount=request.POST.get("refund_amount", "").strip(),
                refund_ref=request.POST.get("refund_ref", "").strip())
            messages.success(request, f"退款紀錄建立成功 (${request.POST.get('refund_amount')})")
        except Exception as e:
            messages.error(request, str(e))
        return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=finance")

@admin_app_func.staff_access_control
@require_POST
def course_generate_schedule(request, hash_course):

    if not (course_id := decode_id(hash_course)):
        messages.error(request, "無法辨識的課程紀錄, 系統已阻擋此操作")
        return redirect('courses:course_list')
    else:  
        obj_course = get_object_or_404(Course, id=course_id)       
        existing_count = CourseSchedule.objects.filter(course_id=course_id).exclude(file_status='deleted').count()
        if existing_count >= obj_course.total_lessons:
            messages.error(request, f"自動產生失敗：目前排期已有 {existing_count} 堂課，已達上限。")
        elif obj_course.period_from and obj_course.period_to and obj_course.total_lessons and obj_course.lesson_weekday:      
            try:
                with transaction.atomic():

                    current_date = obj_course.period_from
                    created_count = 0

                    while current_date <= obj_course.period_to and (existing_count + created_count) < obj_course.total_lessons:
                        if current_date.isoweekday() in obj_course.lesson_weekday:
                            course_app_func.save_course_schedule(
                                obj_course=obj_course, 
                                input_date=current_date, 
                                schedule_id=None,
                                start_time=obj_course.time_from, 
                                end_time=obj_course.time_to,
                                staff_username=request.obj_staff.username)                
                            created_count += 1
                        current_date += timedelta(days=1)

                    messages.success(request, f"成功自動產生 {created_count} 堂課的排期！")
            except Exception:
                messages.error(request, "系統發生錯誤，課程排期已安全撤銷，請聯絡管理員。")
        else:
            messages.error(request, "課程資料不齊全, 請補完資料或手動加入課程排期")     
    return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=schedule")

@admin_app_func.staff_access_control
@require_POST
def course_create_schedule(request, hash_course):
    if not (course_id := decode_id(hash_course)):
        messages.error(request, "無法辨識的課程紀錄, 系統已阻擋此操作。")
        return redirect('courses:course_list')
    else:  
        obj_course = get_object_or_404(Course, id=course_id)
        parsed_date = parse_date(request.POST.get("lesson_date", "").strip())
        parsed_start = parse_time(request.POST.get("start_time", "").strip())
        parsed_end = parse_time(request.POST.get("end_time", "").strip())

        if not parsed_date or not parsed_start or not parsed_end:
            messages.error(request, "請填寫正確的日期與時間格式")
        else:
            try:
                course_app_func.save_course_schedule(
                    obj_course=obj_course, 
                    input_date=parsed_date, 
                    schedule_id=None,#New
                    start_time=parsed_start, 
                    end_time=parsed_end,
                    title=request.POST.get("lesson_title", "").strip(), 
                    content=request.POST.get("lesson_content", "").strip(), 
                    remarks=request.POST.get("remarks", "").strip(),
                    staff_username=request.obj_staff.username)
                messages.success(request, "排期儲存成功！")
            except Exception as e:
                messages.error(request, str(e))
    return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=schedule")

@admin_app_func.staff_access_control
@require_POST
def course_edit_schedule(request, hash_schedule):

    if not (schedule_id := decode_id(hash_schedule)):
        messages.error(request, "無法辨識的課程紀錄, 系統已阻擋此操作。")
        return redirect('courses:course_list')
    else:  
        obj_schedule = get_object_or_404(CourseSchedule, Q(id=schedule_id) & ~Q(file_status="deleted"))
        obj_course = get_object_or_404(Course, Q(id=obj_schedule.course.id) & ~Q(file_status="deleted"))
        hash_course = encode_id(obj_schedule.course_id)

        parsed_date = parse_date(request.POST.get("lesson_date", "").strip())
        parsed_start = parse_time(request.POST.get("start_time", "").strip())
        parsed_end = parse_time(request.POST.get("end_time", "").strip())

        if not parsed_date or not parsed_start or not parsed_end:
            messages.error(request, "請填寫正確的日期與時間格式")
        else:
            try:
                course_app_func.save_course_schedule(
                    obj_course=obj_course, 
                    input_date=parsed_date, 
                    schedule_id=schedule_id,
                    start_time=parsed_start, 
                    end_time=parsed_end,
                    title=request.POST.get("lesson_title", "").strip(), 
                    content=request.POST.get("lesson_content", "").strip(), 
                    remarks=request.POST.get("remarks", "").strip(),
                    staff_username=request.obj_staff.username)
                messages.success(request, "排期儲存成功！")
            except Exception as e:
                messages.error(request, str(e))
        return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=schedule")

@admin_app_func.staff_access_control
@require_POST
def course_delete_schedule(request, hash_schedule):
    if not (schedule_id := decode_id(hash_schedule)):
        messages.error(request, "無法辨識的排期紀錄, 系統已阻擋此操作。")
        return redirect('courses:course_list')
    else:
        obj_schedule = get_object_or_404(CourseSchedule, Q(id=schedule_id) & ~Q(file_status="deleted"))
        hash_course = encode_id(obj_schedule.course_id)
        try:
            obj_schedule.delete()
            messages.success(request, "排期已成功刪除")
        except CourseSchedule.DoesNotExist:
            messages.error(request, "刪除失敗：找不到該筆排期資料")
        return redirect(f"{reverse('courses:course_view', args=[hash_course])}?tab=schedule")