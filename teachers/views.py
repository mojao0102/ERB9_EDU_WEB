from administration.func import app_func as admin_app_func
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Teacher
from datetime import date
from core.utils import decode_id
from .forms import TeacherForm
from django.http import Http404
from courses.func import app_func as course_app_func
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

@admin_app_func.staff_access_control
def teacher_list(request):
    list_teacher = Teacher.objects.exclude(file_status='deleted').order_by('-created_datetime')

    keyword = request.GET.get("txtkeyword", "").strip()
    sort_by = request.GET.get("sort_by", "")
    sort_dir = request.GET.get("sort_dir", "asc")

    filter_active = request.GET.get("filter_active", "")
    if filter_active == "1":
        list_teacher = list_teacher.filter(is_active=True)
    elif filter_active == "0":
        list_teacher = list_teacher.filter(is_active=False)

    if keyword:
        list_teacher = list_teacher.filter(
            Q(teacher_no__icontains=keyword) |
            Q(first_name__icontains=keyword) |
            Q(last_name__icontains=keyword) |
            Q(phone__icontains=keyword) |
            Q(email__icontains=keyword)
        )

    sort_allow = ["teacher_no", "first_name", "title", "phone", "is_active"]
    if sort_by in sort_allow:
        order_field = sort_by if sort_dir == "asc" else f"-{sort_by}"
        list_teacher = list_teacher.order_by(order_field)
    else:
        list_teacher = list_teacher

    paginator = Paginator(list_teacher, 15)
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
        "filter_active": filter_active,
    }

    context = {"page_obj": page_obj, "input_data": input_data}
    return render(request, "teacher_list.html", context)

@admin_app_func.staff_access_control
def teacher_edit(request, hash_teacher=None):

    if hash_teacher:
        teacher_id = decode_id(hash_teacher)
        if not teacher_id:
            raise Http404("無效的導師")
        teacher = get_object_or_404(Teacher, id=teacher_id)
    else:
        teacher=None

    if request.method == 'POST':

        form = TeacherForm(request.POST, instance=teacher)       
        if form.is_valid():
            obj_teacher = form.save(commit=False)
            obj_teacher.last_updated_by = request.obj_staff.username
            obj_teacher.created_by = obj_teacher.created_by if teacher else request.obj_staff.username
            str_success_message = '成功更新導師記錄' if teacher else '成功建立導師記錄'
            str_error_message = '更新導師失敗' if teacher else '建立導師失敗'

            try:
                obj_teacher.save()
                messages.success(request, str_success_message)      
                return redirect('teachers:teacher_list')
            except Exception as e:
                print(f"更新導師失敗: {str(e)}")
                messages.error(request, str_error_message)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:#GET
        form = TeacherForm(instance=teacher)
    return render(request, "teacher_edit.html", {'form': form, 'teacher': teacher})


@admin_app_func.staff_access_control
def teacher_view(request, hash_teacher):

    teacher_id = decode_id(hash_teacher)
    if not teacher_id:
        raise Http404("無效的導師")  

    teacher = get_object_or_404(Teacher, Q(id=teacher_id) & ~Q(file_status='deleted'))

    all_teacher_courses = course_app_func.get_courses_with_dynamic_status(teacher_id=teacher_id).order_by('-period_from')

    context = {
        "teacher": teacher,
        "all_teacher_courses": all_teacher_courses,
    }
    return render(request, "teacher_view.html", context)
