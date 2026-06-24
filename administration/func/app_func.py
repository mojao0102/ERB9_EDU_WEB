from ..models import Staff
from django.utils import timezone
from django.contrib import messages
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.db.models import Q
import os
from ..models import Center
from django.conf import settings
from django.template.loader import render_to_string
from weasyprint import HTML
from django.utils.dateparse import parse_date
from datetime import datetime, time
from decimal import Decimal
import calendar as py_calendar
from django.http import HttpResponse
import csv
from courses.func import app_func as course_app_func

#Decorator for check access
def staff_access_control(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        #Check if login
        if not request.session.get('staff_id'):
            messages.error(request, "請先登入帳號")
            return redirect("administration:staff_login")
        try:#Check if staff
            obj_staff = Staff.objects.get(Q(id=request.session.get('staff_id')) & ~Q(file_status='deleted'))
        except Staff.DoesNotExist:
            messages.error(request, "帳號不存在，請聯絡系統管理員")
            return redirect("administration:staff_login")
        
        #Check if staff active
        if not obj_staff.is_active:
            clear_login_session(request)
            messages.error(request, "帳號已被停權，請聯絡系統管理員")
            return redirect("administration:staff_login")
        
        #For view's function to use
        request.obj_staff = obj_staff
        return view_func(request, *args, **kwargs)    
    return _wrapped_view

# region create login session and update last login
def create_login_session(request, obj_staff):
    request.session['staff_id'] = obj_staff.id
    request.session['staff_name'] = obj_staff.username
    obj_staff.last_login = timezone.localtime(timezone.now())
    obj_staff.save()

# region clear login session
def clear_login_session(request):
    #request.session.flush()
    request.session.pop('staff_id', None)
    request.session.pop('staff_name', None)


def get_filtered_transactions(request):
    #Get default
    _, last_day = py_calendar.monthrange(timezone.now().date().year, timezone.now().date().month)
    default_start = timezone.now().date().replace(day=1)
    default_end = timezone.now().date().replace(day=last_day)

    date_from = parse_date(request.GET.get('date_from', '').strip()) if request.GET.get('date_from', '').strip() else default_start
    date_to = parse_date(request.GET.get('date_to', '').strip()) if request.GET.get('date_to', '').strip() else default_end

    main_cat_id = request.GET.get('MainCategorySelector', '').strip()
    sub_cat_id = request.GET.get('SubCategorySelector', '').strip()
    record_type = request.GET.get('TypeSelector', '').strip()
    trans_method = request.GET.get('MethodSelector', '').strip()
    keyword = request.GET.get('txtkeyword', '').strip()
    sort_by = request.GET.get('sort_by', 'trans_date').strip()
    sort_dir = request.GET.get('sort_dir', 'desc').strip()

    trans_filters = {
        'date_from': date_from,
        'date_to': datetime.combine(date_to, time.max),
        'main_category_id': int(main_cat_id) if main_cat_id else None,
        'sub_category_id': int(sub_cat_id) if sub_cat_id else None,
        'trans_method': trans_method if trans_method else None,
        'keyword': keyword,
        'record_type' : record_type,
    }

    list_trans = course_app_func.get_transaction_list(**trans_filters) or []#Prevent empty list return
    total_payment, count_payment = Decimal('0.00'), 0
    total_refund, count_refund = Decimal('0.00'), 0

    for dict_trans in list_trans:
        amount = Decimal(str(dict_trans['trans_amount'] or '0.00'))
        if dict_trans['record_type'] == 'payment':
            total_payment += amount
            count_payment += 1
        elif dict_trans['record_type'] == 'refund':
            total_refund += amount
            count_refund += 1

    net_income = total_payment - total_refund

    reverse_flag = True if sort_dir == 'desc' else False   
    if sort_by in ['trans_date', 'trans_amount', 'trans_method']:
        list_trans.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse_flag)
    elif sort_by == 'student_name':
        list_trans.sort(key=lambda x: (x.get('student_cn') or x.get('student_en') or '').lower(), reverse=reverse_flag)
    elif sort_by == 'course_name':
        list_trans.sort(key=lambda x: (x.get('course_name') or '').lower(), reverse=reverse_flag)

    dict_input_data = {
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'MainCategorySelector': main_cat_id,
        'SubCategorySelector': sub_cat_id,
        'TypeSelector': record_type,
        'MethodSelector': trans_method,
        'txtkeyword': keyword,
        'sort_by': sort_by,
        'sort_dir': sort_dir,}
    return list_trans, dict_input_data, total_payment, total_refund, net_income, count_payment, count_refund


def generate_transaction_report_pdf(list_trans, dict_input_data, total_payment, total_refund, net_income, count_payment, count_refund):
    obj_center = Center.objects.first()       
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo', 'logo.png')
    logo_url = f"file://{logo_path}" if os.path.exists(logo_path) else ""

    # 準備傳給 PDF 模板的資料包
    context = {
        'list_trans': list_trans,
        'dict_input_data': dict_input_data,
        'total_payment': total_payment,
        'total_refund': total_refund,
        "count_payment": count_payment,
        "count_refund": count_refund,
        'net_income': net_income,
        'obj_center': obj_center,
        'logo_url': logo_url,
        'generate_time': timezone.now()}   
    # 渲染 HTML 並轉換為 PDF Bytes
    html_string = render_to_string('report_template/transaction_report.html', context)
    pdf_bytes = HTML(string=html_string).write_pdf()
    
    return pdf_bytes
