from administration.func import app_func as admin_app_func
from administration.models import Room
from ..models import Course, CourseMainCategory, CourseSubCategory, CourseTemplate, SignUp, SignUpRefund, CourseSchedule
from django.http import HttpResponse
from teachers.models import Teacher
from django.db.models import Q, F, Prefetch, Sum, Count, Case, When, Value, CharField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..func import app_func as course_app_func
from django.utils.dateparse import parse_date
from datetime import datetime, time
from core.utils import decode_id
from django.http import Http404
from django.db import transaction
from decimal import Decimal
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# region Course
@admin_app_func.staff_access_control
def course_list(request):
    
    #Load Category for filter
    list_maincategory = CourseMainCategory.objects.filter(is_active=True)
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).select_related("main_category")
    
    course_filters = {} 
    if keyword:= request.GET.get('txtkeyword', '').strip():
        course_filters['keyword'] = keyword
    if maincourse_category:= request.GET.get('MainCategorySelector', '').strip():
        course_filters['sub_category__main_category_id'] = maincourse_category
    if subcourse_category:= request.GET.get('SubCategorySelector', '').strip():
        course_filters['sub_category_id'] = subcourse_category
    if (publish_status := request.GET.get('PublishSelector', '').strip()) in ('0', '1'):
        course_filters['is_web_publish'] = (publish_status == '1')
    if (promote_status := request.GET.get('PromoteSelector', '').strip()) in ('0', '1'):
        course_filters['is_promote'] = (promote_status == '1')
    if start_date_from:= parse_date(request.GET.get('start_date_from', '').strip()):
        course_filters['period_from__gte'] = start_date_from
    if start_date_to:= parse_date(request.GET.get('start_date_to', '').strip()):
        course_filters['period_from__lte'] = start_date_to
    if expiry_date_from:= parse_date(request.GET.get('expiry_date_from', '').strip()):
        course_filters['registation_expiry_date__gte'] = expiry_date_from
    if expiry_date_to:= parse_date(request.GET.get('expiry_date_to', '').strip()):
        course_filters['registation_expiry_date__lte'] = datetime.combine(expiry_date_to, time.max)

    list_course = course_app_func.get_courses_with_dynamic_status(**course_filters)\
    .annotate(
        schedule_count=Count('courseschedule', filter=~Q(file_status='deleted'), distinct=True),
        schedule_status=Case(
            When(schedule_count=0, then=Value('未安排')),
            When(schedule_count__gte=F('total_lessons'), then=Value('已安排')),
            When(schedule_count__lt=F('total_lessons'), then=Value('部分安排')),
            default=Value('未安排'), output_field=CharField())).select_related("sub_category__main_category", "teacher")
    
    if schedule_status_filter := request.GET.get('ScheduleStatusSelector', '').strip():
        if schedule_status_filter == '未安排/部分安排':
            list_course = list_course.filter(schedule_status__in=('未安排', '部分安排'))
        elif schedule_status_filter == '已安排':
            list_course = list_course.filter(schedule_status=schedule_status_filter)

    if has_signup_filter := request.GET.get('HasSignupSelector', '').strip():
        if has_signup_filter == "1":
            list_course = list_course.filter(current_signup_count__gt=0)
        elif has_signup_filter == "0":
            list_course = list_course.filter(current_signup_count=0)

    if has_cancelled_filter := request.GET.get('HasCancelledSelector', '').strip():
        if has_cancelled_filter == "1":
            list_course = list_course.filter(cancelled_signup_count__gt=0)
        elif has_cancelled_filter == "0":
            list_course = list_course.filter(cancelled_signup_count=0)

    if has_refund_filter := request.GET.get('HasRefundSelector', '').strip():
        if has_refund_filter == "1":
            list_course = list_course.filter(refund_record_count__gt=0)
        elif has_refund_filter == "0":
            list_course = list_course.filter(refund_record_count=0)

    if 'StatusSelector' in request.GET:
        list_selected_status = request.GET.getlist('StatusSelector')
    elif request.GET.get('clear_status') == '1':
        list_selected_status = []
    else:
        list_selected_status = ['報名中', '人數已滿', '截止報名', '進行中']
    if list_selected_status and '' not in list_selected_status:
        list_course = list_course.filter(course_dynamic_status__in=list_selected_status)

    #Sorting
    sort_by = request.GET.get('sort_by', '').strip()
    sort_dir = request.GET.get('sort_dir', 'asc').strip()
    if sort_by:
        valid_sort_fields = ['code', 'name', 'is_web_publish', 'is_promote', 'registation_expiry_date', 'period_from', 'period_to', 'sub_category__name', "teacher__title", "schedule_status"]
        if sort_by in valid_sort_fields:
            order_prefix = '-' if sort_dir == 'desc' else ''
            list_course = list_course.order_by(f"{order_prefix}{sort_by}")

    request.GET.getlist_StatusSelector = list_selected_status
    
    #Paginator
    paginator = Paginator(list_course, 10) 
    page_number = request.GET.get('page', 1)   
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)      

    context = {
        "list_maincategory" : list_maincategory, 
        "list_subcategory" : list_subcategory, 
        "list_course" : page_obj, 
        "input_data" : request.GET}   
    return render(request, "courses/course_list.html", context)

@admin_app_func.staff_access_control
def course_create(request):

    list_templates = CourseTemplate.objects.exclude(file_status="deleted")
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).exclude(file_status="deleted")
    list_teacher = Teacher.objects.filter(is_active=True).exclude(file_status="deleted")
    list_room = Room.objects.exclude(file_status="deleted")

    if request.method == "POST":

        #Check input Valid
        blnIsValid, parsed_data = course_app_func.validate_and_parse_course_form(request)      
        if not blnIsValid:
            context = {
                "form_mode" : "create",
                "list_templates": list_templates,
                "list_subcategory": list_subcategory,
                "list_teacher": list_teacher,
                "list_room": list_room,
                "obj_course" : parsed_data,}
            return render(request, "courses/course_edit.html", context)

        #ORM Create
        obj_course = Course.objects.create(
            sub_category_id=parsed_data.get("sub_category_id"),
            teacher_id=parsed_data.get("teacher_id"),
            # center_id=parsed_data.get("center_id"),
            
            #code=parsed_data.get("code"),
            code=course_app_func.generate_course_code(parsed_data.get("sub_category_id")),
            name=parsed_data.get("name"),
            content=parsed_data.get("content"),
            photo=request.FILES.get("photo"),
            age_group=parsed_data.get("age_group", ""),

            feature_1=parsed_data.get("feature_1", ""),
            feature_2=parsed_data.get("feature_2", ""),
            feature_3=parsed_data.get("feature_3", ""),
            feature_4=parsed_data.get("feature_4", ""),
            feature_5=parsed_data.get("feature_5", ""),
            feature_6=parsed_data.get("feature_6", ""),
            feature_7=parsed_data.get("feature_7", ""),
            feature_8=parsed_data.get("feature_8", ""),
            
            course_fee=parsed_data.get("course_fee", 0),
            total_lessons=parsed_data.get("total_lessons", 0),
            hours_per_lesson=parsed_data.get("hours_per_lesson") or 0,
            max_no_student=parsed_data.get("max_no_student", 0),
            
            period_from=parsed_data.get("period_from"),
            period_to=parsed_data.get("period_to"),
            time_from=parsed_data.get("time_from"),
            time_to=parsed_data.get("time_to"),
            
            is_mon=parsed_data.get("is_mon", False),
            is_tue=parsed_data.get("is_tue", False),
            is_wed=parsed_data.get("is_wed", False),
            is_thu=parsed_data.get("is_thu", False),
            is_fri=parsed_data.get("is_fri", False),
            is_sat=parsed_data.get("is_sat", False),
            is_sun=parsed_data.get("is_sun", False),
            
            default_room_id=parsed_data.get("room_id"),
            registation_expiry_date=parsed_data.get("registation_expiry_date"),
            is_web_publish=parsed_data.get("is_web_publish", False),
            is_promote=parsed_data.get("is_promote", False),
            course_status="created",
            created_by=request.obj_staff.username,
        )
        #Success
        messages.success(request, "課程建立成功！")
        return redirect("courses:course_view", obj_course.hash_id)
    else:
        context = {
            "form_mode" : "create",
            "list_templates": list_templates,
            "list_subcategory": list_subcategory,
            "list_teacher": list_teacher,
            "list_room": list_room,}
        
        #Check if course template id
        if (hash_template_id:= request.GET.get("template_id", '').strip()):
            template_id = decode_id(hash_template_id)
            if not template_id:
                raise Http404("無效的課程範本")       
            obj_tempcourse = get_object_or_404(CourseTemplate, Q(id=template_id) & ~Q(file_status='deleted'))

            context['obj_course'] = {
                "name": obj_tempcourse.name,
                "content": obj_tempcourse.content,
                "sub_category_id": obj_tempcourse.sub_category_id,
                "teacher_id": obj_tempcourse.teacher_id,
                "course_fee": obj_tempcourse.course_fee,
                "total_lessons": obj_tempcourse.total_lessons,
                "hours_per_lesson": obj_tempcourse.hours_per_lesson,
                "feature_1": obj_tempcourse.feature_1,
                "feature_2": obj_tempcourse.feature_2,
                "feature_3": obj_tempcourse.feature_3,
                "feature_4": obj_tempcourse.feature_4,
                "feature_5": obj_tempcourse.feature_5,
                "feature_6": obj_tempcourse.feature_6,
                "feature_7": obj_tempcourse.feature_7,
                "feature_8": obj_tempcourse.feature_8,
                "is_web_publish": True, # 預設開啟發佈
            }
            messages.info(request, f"已成功載入範本《{obj_tempcourse.name}》的預設資料")


        return render(request, "courses/course_edit.html", context)

@admin_app_func.staff_access_control
def course_edit(request, hash_course):
    #decode hash id
    course_id = decode_id(hash_course)
    if not course_id:
        raise Http404("無效的課程連結")
    
    obj_course = get_object_or_404(Course, Q(id=course_id) & ~Q(file_status="deleted"))
    list_templates = CourseTemplate.objects.exclude(file_status="deleted")
    list_subcategory = CourseSubCategory.objects.filter(is_active=True).exclude(file_status="deleted")
    list_teacher = Teacher.objects.filter(is_active=True).exclude(file_status="deleted")
    list_room = Room.objects.exclude(file_status="deleted")

    if request.method == "POST":
        #Check if delete      
        if request.POST.get("btnAction", '').strip() == "delete":
            if SignUp.objects.filter(course_id=course_id).exclude(file_status="deleted").exists():
                messages.error(request, "此課程已有學生報名，無法刪除，請考慮將狀態改為取消")
                return redirect("courses:course_edit", hash_course)
            else:
                obj_course = get_object_or_404(Course, (Q(id=course_id) & ~Q(file_status="deleted")))
                obj_course.delete()
                messages.success(request, "Deleted")
                return redirect("courses:course_list")
            
        #Check if cancel      
        if request.POST.get("btnAction", '').strip() == "cancel":
            if not request.obj_staff.is_admin:
                messages.error(request, "權限不足：只有管理員才能取消課程。")
                return redirect("courses:course_edit", hash_course)
            else:
                #Check if staff input cancel reason
                if not (cancel_reason := request.POST.get("cancel_reason", "").strip()):
                    messages.error(request, "請填寫或選擇課程取消的原因。")
                    return redirect("courses:course_edit", hash_course)
                try:
                    with transaction.atomic():
                        #Update course's course_status to cancel
                        obj_course.course_status = 'cancel'
                        obj_course.last_updated_by=request.obj_staff.username
                        obj_course.save()
                        #Update signup's sign_up_status to cancel 
                        blnIsSuccess, updated_count = course_app_func.cancel_signup(
                            request=request, 
                            course_id=course_id, 
                            cancel_reason=cancel_reason)
                        
                        if blnIsSuccess:
                            messages.success(request, f"課程已成功取消！系統已連動取消 {updated_count} 位學生的報名紀錄。")
                            return redirect("courses:course_edit", hash_course)
                        else:
                            raise Exception("連動取消學生報名失敗")     
                except Exception as e:
                    print(f"取消課程失敗: {str(e)}")
                    return redirect("courses:course_edit", hash_course)

        #Edit, load datasource
        obj_course = get_object_or_404(Course, Q(id=course_id) & ~Q(file_status="deleted"))

        #Check input Valid
        blnIsValid, parsed_data = course_app_func.validate_and_parse_course_form(request)      
        if not blnIsValid:
            parsed_data['hash_id'] = hash_course
            context = {
                "form_mode" : "edit",
                "obj_course": parsed_data,
                "list_templates": list_templates,
                "list_subcategory": list_subcategory,
                "list_teacher": list_teacher,
                "list_room": list_room,}
            return render(request, "courses/course_edit.html", context)
        
        # Update object
        obj_course.sub_category_id = parsed_data.get("sub_category_id")
        obj_course.teacher_id = parsed_data.get("teacher_id")
        # obj_course.center_id = parsed_data.get("center_id")
        obj_course.code = parsed_data.get("code")
        obj_course.name = parsed_data.get("name")
        obj_course.content = parsed_data.get("content")

        obj_course.age_group=parsed_data.get("age_group", "")

        if "photo" in request.FILES:
            obj_course.photo = request.FILES.get("photo")
            
        obj_course.feature_1 = parsed_data.get("feature_1", "")
        obj_course.feature_2 = parsed_data.get("feature_2", "")
        obj_course.feature_3 = parsed_data.get("feature_3", "")
        obj_course.feature_4 = parsed_data.get("feature_4", "")
        obj_course.feature_5 = parsed_data.get("feature_5", "")
        obj_course.feature_6 = parsed_data.get("feature_6", "")
        obj_course.feature_7 = parsed_data.get("feature_7", "")
        obj_course.feature_8 = parsed_data.get("feature_8", "")
        
        obj_course.course_fee = parsed_data.get("course_fee", 0)
        obj_course.total_lessons = parsed_data.get("total_lessons", 0)
        obj_course.hours_per_lesson = parsed_data.get("hours_per_lesson") or 0
        obj_course.max_no_student = parsed_data.get("max_no_student", 0)
        
        obj_course.period_from = parsed_data.get("period_from")
        obj_course.period_to = parsed_data.get("period_to")
        obj_course.time_from = parsed_data.get("time_from")
        obj_course.time_to = parsed_data.get("time_to")
        
        obj_course.is_mon = parsed_data.get("is_mon", False)
        obj_course.is_tue = parsed_data.get("is_tue", False)
        obj_course.is_wed = parsed_data.get("is_wed", False)
        obj_course.is_thu = parsed_data.get("is_thu", False)
        obj_course.is_fri = parsed_data.get("is_fri", False)
        obj_course.is_sat = parsed_data.get("is_sat", False)
        obj_course.is_sun = parsed_data.get("is_sun", False)
        
        obj_course.default_room_id=parsed_data.get("room_id")
        obj_course.registation_expiry_date = parsed_data.get("registation_expiry_date")
        obj_course.is_web_publish = parsed_data.get("is_web_publish", False)
        obj_course.is_promote = parsed_data.get("is_promote", False)
        obj_course.last_updated_by=request.obj_staff.username

        obj_course.save()
        messages.success(request, "課程更新成功！")
        return redirect("courses:course_view", hash_course)
    
    else:#GET
        course_queryset = Course.objects.exclude(file_status="deleted").prefetch_related(
            Prefetch("courseschedule_set",queryset=CourseSchedule.objects.exclude(file_status='deleted').order_by('lesson_date', 'start_time')))
        obj_course = get_object_or_404(course_queryset, id=course_id)

        context = {
            "form_mode" : "edit",
            "obj_course": obj_course,
            "list_templates": list_templates,
            "list_subcategory": list_subcategory,
            "list_teacher": list_teacher,
            "list_room": list_room,}
        return render(request, "courses/course_edit.html", context)
# endregion

@admin_app_func.staff_access_control
def course_view(request, hash_course):

    #decode hash id
    course_id = decode_id(hash_course)
    if not course_id:
        raise Http404("無效的課程連結")
    
    course_queryset = course_app_func.get_courses_with_dynamic_status(id=course_id)\
    .select_related("sub_category__main_category", "default_room", "teacher")\
    .prefetch_related(
        Prefetch("signup_set", queryset=SignUp.objects
                .exclude(file_status="deleted")
                .annotate(total_refund_amount=Sum('signuprefund__refund_amount', filter=~Q(signuprefund__file_status='deleted')))
                .select_related("student")),
        Prefetch("courseschedule_set", queryset=CourseSchedule.objects.exclude(file_status="deleted")))

    obj_course = course_queryset.first()
    if not obj_course:
        raise Http404("找不到該課程")
    
    #Get Course trans list
    list_trans = course_app_func.get_transaction_list(**{"course_id" : course_id}) or []

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
        "obj_course": obj_course, 
        #"list_signup": list_signup, 
        "list_trans": list_trans,
        "total_payment": total_payment,
        "total_refund": total_refund,
        "net_income": net_income}
    
    return render(request, "courses/course_view.html", context)