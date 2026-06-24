from administration.func import app_func as admin_app_func
from ..models import Course, CourseMainCategory, CourseSubCategory, CourseTemplate, SignUp, SignUpRefund, CourseSchedule
from django.http import HttpResponse
from teachers.models import Teacher
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.utils import decode_id
from django.http import Http404
from ..forms import CourseTemplateForm

# region CourseTemplate
def _template_context():
    return {
        'sub_categories': CourseSubCategory.objects.select_related('main_category').filter(is_active=True),
        'teachers': Teacher.objects.filter(is_active=True),
    }

@admin_app_func.staff_access_control
def coursetemp_list(request):
    list_template = CourseTemplate.objects.exclude(file_status='deleted').select_related('teacher', 'sub_category__main_category').all()

    if (keyword:= request.GET.get('keyword', '').strip()):
        list_template = list_template.filter(name__icontains=keyword)

    if (cat:= request.GET.get('category', '').strip()):
        list_template = list_template.filter(sub_category_id=cat)

    sub_categories = CourseSubCategory.objects.select_related('main_category').filter(is_active=True)

    return render(request, "courses/coursetemp_list.html", {
        'templates': list_template,
        'sub_categories': sub_categories,
        'keyword': keyword,
        'selected_category': cat,
    })

@admin_app_func.staff_access_control
def coursetemp_create(request):
    if request.method == 'POST':
        form = CourseTemplateForm(request.POST)
        if form.is_valid():
            tmpl = form.save(commit=False)
            tmpl.created_by = request.obj_staff.username
            tmpl.last_updated_by = request.obj_staff.username
            tmpl.save()
            messages.success(request, "新增成功")
            return redirect('courses:coursetemp_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")                   
    context = _template_context()
    context['features'] = [''] * 8
    return render(request, "courses/coursetemp_edit.html", context)

@admin_app_func.staff_access_control
def coursetemp_edit(request, hash_template):
    template_id = decode_id(hash_template)
    if not template_id:
        raise Http404("無效的課程範本")   

    tmpl = get_object_or_404(CourseTemplate, id=template_id)
    
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            tmpl.delete()
            messages.success(request, "刪除成功")
            return redirect('courses:coursetemp_list')
            
        form = CourseTemplateForm(request.POST, instance=tmpl)
        if form.is_valid():
            obj_tmpl = form.save(commit=False)
            obj_tmpl.last_updated_by = request.obj_staff.username
            obj_tmpl.save()
            messages.success(request, "更新成功")
            return redirect('courses:coursetemp_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    context = _template_context()
    context['template'] = tmpl
    context['features'] = [getattr(tmpl, f'feature_{i}') for i in range(1, 9)]
    return render(request, "courses/coursetemp_edit.html", context)

@admin_app_func.staff_access_control
def coursetemp_delete(request, hash_template):
    template_id = decode_id(hash_template)
    if not template_id:
        raise Http404("無效的課程範本")   

    tmpl = get_object_or_404(CourseTemplate, id=template_id)

    try:
        tmpl.delete()
        messages.success(request, "成功刪除課程範本")
        return redirect('courses:coursetemp_list')
    except Exception as e:
        print(f"刪除課程範本失敗: {str(e)}")
        messages.error(request, "刪除課程範本失敗，請聯絡系統管理員")
    return redirect('courses:coursetemp_edit', hash_template)
# endregion