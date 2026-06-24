from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from .models import Staff
from .func import app_func as admin_app_func
from courses.models import CourseMainCategory, CourseSubCategory,  CourseSchedule
from administration.func import app_func as admin_app_func
from django.http import HttpResponse
import csv
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from courses.func import app_func as course_app_func
from datetime import datetime, time
from decimal import Decimal
from django.utils.dateparse import parse_date, parse_time
from datetime import datetime, time
from django.utils import timezone

def staff_login(request):

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            obj_staff = Staff.objects.get(Q(username=username) & Q(password=password) & Q(is_active=True) & ~Q(file_status="deleted"))    
            admin_app_func.create_login_session(request, obj_staff)
            return redirect('administration:schedule_list')
        
        except Staff.DoesNotExist:
            admin_app_func.clear_login_session(request)
            messages.error(request, '帳號或密碼錯誤，或沒有權限')
            return render(request, 'staff_login.html', {'input_data': request.POST})
        
        except Exception as e:
            print(f"staff login error, username:{username}, error:{e}")
            messages.error(request, '系統帳號異常，請聯絡中心管理員')
            return render(request, 'staff_login.html', {'input_data': request.POST})
    else:
        return render(request, 'staff_login.html')


@admin_app_func.staff_access_control
def staff_logout(request):
    if request.method == 'POST':
        admin_app_func.clear_login_session(request)
        messages.success(request, '登出成功')
        return redirect('administration:staff_login')
    else:    
        return redirect('administration:staff_dashboard')

@admin_app_func.staff_access_control
def dashboard(request):
    # 取得年份、月份（預設抓現在）
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month

    # 依然抓整年資料（確保年度走勢圖 1-12 月數據完整）
    year_start = datetime(year, 1, 1).date()
    year_end = datetime(year, 12, 31).date()

    trans_filters = {
        'date_from': year_start,
        'date_to': datetime.combine(year_end, time.max),
    }
    
    list_raw_trans = course_app_func.get_transaction_list(**trans_filters) or []

    # 初始化統計變數
    monthly_net_income = Decimal('0.00')
    monthly_payment_amount, monthly_payment_count = Decimal('0.00'), 0
    monthly_refund_amount, monthly_refund_count = Decimal('0.00'), 0
    monthly_students = set()
    monthly_signup_total = 0

    yearly_net_income = Decimal('0.00')
    yearly_payment_amount, yearly_payment_count = Decimal('0.00'), 0
    yearly_refund_amount, yearly_refund_count = Decimal('0.00'), 0
    yearly_students = set()
    yearly_signup_total = 0

    month_revenue_list = [0.0] * 12
    category_stats = {}

    for trans in list_raw_trans:
        t_date = trans.get('trans_date')
        if not t_date:
            continue
            
        t_month = t_date.month
        amount = Decimal(str(trans.get('trans_amount') or '0.00'))
        record_type = trans.get('record_type')
        student_no = trans.get('student_no')
        
        main_cat = trans.get('main_category_short') or '未分類'
        sub_cat = trans.get('sub_category_name') or '未分類'
        cat_key = f"[{main_cat}] {sub_cat}"

        net = amount if record_type == 'payment' else -amount

        # 1. 年度數據與趨勢圖累積
        yearly_net_income += net
        if record_type == 'payment':
            yearly_payment_amount += amount
            yearly_payment_count += 1
            yearly_signup_total += 1
            if student_no:
                yearly_students.add(student_no)
        elif record_type == 'refund':
            yearly_refund_amount += amount
            yearly_refund_count += 1
        
        month_revenue_list[t_month - 1] += float(net)

        # 2. 精準綁定：月度卡片與排行
        if t_month == month:
            monthly_net_income += net
            if record_type == 'payment':
                monthly_payment_amount += amount
                monthly_payment_count += 1
                monthly_signup_total += 1
                if student_no:
                    monthly_students.add(student_no)
            elif record_type == 'refund':
                monthly_refund_amount += amount
                monthly_refund_count += 1
            
            # 類別排行統計
            if cat_key not in category_stats:
                category_stats[cat_key] = {'name': cat_key, 'signups': 0, 'net_income': Decimal('0.00')}
            
            category_stats[cat_key]['net_income'] += net
            if record_type == 'payment':
                category_stats[cat_key]['signups'] += 1

    top_categories = sorted(category_stats.values(), key=lambda x: x['net_income'], reverse=True)

    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    current_year = timezone.now().year
    years = [current_year - 1, current_year, current_year + 1]
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'active_page': 'dashboard',
        'year': year,
        'month': month,
        'years': years,
        'months': months,

        # 當月數據
        'monthly_revenue': monthly_net_income,
        'monthly_payment_amount': monthly_payment_amount,
        'monthly_payment_count': monthly_payment_count,
        'monthly_refund_amount': monthly_refund_amount,
        'monthly_refund_count': monthly_refund_count,
        'monthly_student_distinct': len(monthly_students),
        'monthly_signup_total': monthly_signup_total,

        # 當年數據
        'yearly_revenue': yearly_net_income,
        'yearly_payment_amount': yearly_payment_amount,
        'yearly_payment_count': yearly_payment_count,
        'yearly_refund_amount': yearly_refund_amount,
        'yearly_refund_count': yearly_refund_count,
        'yearly_student_distinct': len(yearly_students),
        'yearly_signup_total': yearly_signup_total,

        'chart_labels': month_labels,
        'chart_data': month_revenue_list,
        'top_categories': top_categories[:10],
    }

    return render(request, 'staff_dashboard.html', context)

@admin_app_func.staff_access_control
def transaction_list(request):

    # Set filter datasource
    list_maincategory = CourseMainCategory.objects.filter(is_active=True)
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).select_related("main_category")

    list_trans, dict_input_data, total_payment, total_refund, net_income, count_payment, count_refund = admin_app_func.get_filtered_transactions(request)
    
    paginator = Paginator(list_trans, 10) 
    page_number = request.GET.get('page', 1)   
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "list_maincategory": list_maincategory,
        "list_subcategory": list_subcategory,
        "page_obj": page_obj,
        "total_payment": total_payment,
        "total_refund": total_refund,
        "count_payment": count_payment,
        "count_refund": count_refund,
        "net_income": net_income,
        "dict_input_data": dict_input_data}
    
    return render(request, "transaction_list.html", context)

@admin_app_func.staff_access_control
def transaction_export_csv(request):
    list_trans, dict_input_data, *_ = admin_app_func.get_filtered_transactions(request)
    
    date_from = dict_input_data['date_from'].replace("-", "")
    date_to = dict_input_data['date_to'].replace("-", "")
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'Transactions_{date_from}_{date_to}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['交易時間', '學生姓名', '學號', '類型', '金額', '課程類別', '課程名稱', '課程代碼', '交易方式', '參考單號', 'Stripe Session', '報名狀態'])
    
    for dict_trans in list_trans:
        cat_str = f"[{dict_trans['main_category_short']}] {dict_trans['sub_category_name']}" if dict_trans['main_category_short'] else ''
        time_str = dict_trans['trans_date'].strftime('%Y-%m-%d %H:%M') if dict_trans['trans_date'] else ''
        writer.writerow([
            time_str,
            dict_trans['student_cn'] or dict_trans['student_en'],
            dict_trans['student_no'],
            '收款' if dict_trans['record_type'] == 'payment' else '退款',
            dict_trans['trans_amount'],
            cat_str,
            dict_trans['course_name'],
            dict_trans['course_code'],
            dict_trans['trans_method'],
            dict_trans['trans_ref'],
            dict_trans['online_payment_session'],
            dict_trans['signup_status']
        ])
    return response


@admin_app_func.staff_access_control
def transaction_export_pdf(request):
    list_trans, dict_input_data, total_payment, total_refund, net_income, count_payment, count_refund = admin_app_func.get_filtered_transactions(request)
    
    date_from = dict_input_data['date_from'].replace("-", "")
    date_to = dict_input_data['date_to'].replace("-", "")

    pdf_bytes = admin_app_func.generate_transaction_report_pdf(
        list_trans, 
        dict_input_data, 
        total_payment, 
        total_refund, 
        net_income,
        count_payment,
        count_refund)
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f'Transaction_Report_{date_from}_{date_to}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@admin_app_func.staff_access_control
def schedule_list(request):
    today = timezone.now().date()
    
    str_date_from = request.GET.get('date_from', '')
    str_date_to = request.GET.get('date_to', '')
    
    date_from = parse_date(str_date_from) if str_date_from else today
    date_to = parse_date(str_date_to) if str_date_to else today

    list_schedule = CourseSchedule.objects\
                        .exclude(file_status='deleted')\
                        .exclude(course__course_status='cancel', course__file_status='deleted')\
                        .select_related('course', 'course__teacher', 'course__default_room')
    
    list_schedule = list_schedule.filter(lesson_date__date__gte=date_from, lesson_date__date__lte=date_to)

    keyword = request.GET.get('txtkeyword', '').strip()
    if keyword:
        list_schedule = list_schedule.filter(
            Q(course__name__icontains=keyword) |
            Q(course__code__icontains=keyword) |
            Q(lesson_title__icontains=keyword) |
            Q(course__teacher__first_name__icontains=keyword) |
            Q(course__teacher__last_name__icontains=keyword) |
            Q(course__default_room__name__icontains=keyword) )

    sort_by = request.GET.get('sort_by', 'lesson_date')
    sort_dir = request.GET.get('sort_dir', 'asc')
    
    valid_sort_fields = ['lesson_date', 'start_time', 'course__name', 'course__teacher__first_name', 'course__default_room__name']
    if sort_by in valid_sort_fields:
        order_prefix = '-' if sort_dir == 'desc' else ''
        list_schedule = list_schedule.order_by(f"{order_prefix}{sort_by}", f"{order_prefix}start_time")
    else:
        list_schedule = list_schedule.order_by('lesson_date', 'start_time')

    paginator = Paginator(list_schedule, 15) 
    page_number = request.GET.get('page', 1)   
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    dict_input_data = {
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'txtkeyword': keyword,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
    }

    context = {
        'page_obj': page_obj,
        'dict_input_data': dict_input_data,
        'total_count': paginator.count
    }
    
    return render(request, "schedule_list.html", context)

