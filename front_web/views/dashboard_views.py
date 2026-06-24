from django.utils import timezone
from django.db.models import F, Value, CharField, ExpressionWrapper, DateTimeField
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from courses.models import Course, SignUp, SignUpRefund
from ..func import app_func as frontweb_app_func
from courses.func import app_func as course_app_func

from core.utils import decode_id, encode_id
from django.http import Http404

import stripe

# region View: Dashboard
@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_dashboard(request):
    list_mode = "CurrentCourse" if (request.GET.get("ListMode") != "PastCourse" and request.GET.get("ListMode") != "PaymentHistory") else "PastCourse" if request.GET.get("ListMode") == "PastCourse" else "PaymentHistory"
    print(list_mode)
    context = {'list_mc' : request.list_mc, "list_mode" : list_mode}

    if list_mode == "CurrentCourse":

        student_filters = {
        'signup__student_id': request.session.get('student_id'),
        'signup__sign_up_status': 'success',
        'signup__cancel_date__isnull': True,
        'course_status': 'created'}       
        context["list_course"] = course_app_func.get_courses_with_dynamic_status(**student_filters).exclude(course_dynamic_status='已完結')

        # context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        # ).filter(signup__student_id=request.session.get('student_id'), 
        #         signup__sign_up_status='success',
        #         signup__cancel_date__isnull=True,
        #         course_end_datetime__gte=timezone.localtime(timezone.now()),
        #         course_status='created')
        
    elif list_mode == "PastCourse":

        student_filters = {
        'signup__student_id': request.session.get('student_id'),
        'signup__sign_up_status': 'success',
        'signup__cancel_date__isnull': True,
        'course_status': 'created'}       
        context["list_course"] = course_app_func.get_courses_with_dynamic_status(**student_filters).filter(course_dynamic_status='已完結')

        # context["list_course"] = Course.objects.annotate(course_end_datetime=ExpressionWrapper(F('period_to') + F('time_to'), output_field=DateTimeField())
        # ).filter(signup__student_id=request.session.get('student_id'), 
        #         signup__sign_up_status='success',
        #         signup__cancel_date__isnull=True,
        #         course_end_datetime__lte=timezone.localtime(timezone.now()),
        #         course_status='created')
        
    elif list_mode == "PaymentHistory":
        list_trans = course_app_func.get_transaction_list(**{'student_id' : request.session.get('student_id')})
        context["list_trans"] = list_trans

    return render(request, "student_dashboard.html", context)

@frontweb_app_func.student_access_control()
def download_payment_receipt(request, hash_signup):

    signup_id = decode_id(hash_signup)
    if not signup_id:
        raise Http404("無效的連結")

    obj_signup = get_object_or_404(SignUp, id=signup_id)
    
    pdf_bytes = course_app_func.generate_payment_receipt_pdf(obj_signup)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_signup.payment_ref}.pdf"'
    
    return response

@frontweb_app_func.student_access_control()
def download_refund_receipt(request, hash_refund):

    refund_id = decode_id(hash_refund)
    if not refund_id:
        raise Http404("無效的連結")

    obj_refund = get_object_or_404(SignUpRefund, id=refund_id)
    
    pdf_bytes = course_app_func.generate_refund_receipt_pdf(obj_refund)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Receipt_{obj_refund.refund_ref}.pdf"'
    
    return response
# endregion