from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from courses.models import Course, SignUp
from students.models import Student
from ..func import app_func as frontweb_app_func, stripe_func
from courses.func import app_func as course_app_func
import stripe

from core.utils import decode_id
from django.http import Http404
from django.db import transaction


# region View: Course SignUp/Payment
@frontweb_app_func.student_access_control()
def course_payment(request, hash_course):

    course_id = decode_id(hash_course)
    if not course_id:
        raise Http404("無效的連結")

    if request.method == "POST":

        #1 Get course and check if course still avaliable, Only course with status "created", web published, signup number < max no and not over registation expiry date allow to sign_up
        course_filters = {"course_status" : "created", "id" : course_id, "is_web_publish" : True, "registation_expiry_date__gte" : timezone.now()}
        obj_course = course_app_func.get_courses_with_dynamic_status(**course_filters).filter(course_dynamic_status=("報名中")).first()
        if not obj_course:
            messages.error(request, "課程狀態已更改，請刷新頁面")
            return redirect('front_web:course', hash_course)
        
        # Check if student signup already
        if SignUp.objects.filter(course_id=obj_course.id, student_id=request.session['student_id'], sign_up_status="success", cancel_date__isnull=True).exists():
            messages.error(request, "您已報名參加此課程")
            return redirect('front_web:course', hash_course)

        # Check if stripe key define at setting
        if not settings.STRIPE_SECRET_KEY:
            messages.error(request, "付款系統出錯，請聯絡本中心")
            return redirect('front_web:course', hash_course)
        
        # stripe progress
        try:
            with transaction.atomic():
                
                # 取得最原始的 Course 物件並將這一行資料鎖死，直到整個 with 區塊結束
                try:
                    locked_course = Course.objects.select_for_update().get(
                        id=course_id, 
                        course_status="created", 
                        is_web_publish=True
                    )
                except Course.DoesNotExist:
                    messages.error(request, "課程狀態已更改，無法報名")
                    return redirect('front_web:course', hash_course)

                # 拿到鎖之後，在這個當下重新即時計算「已成功報名」的人數
                current_count = SignUp.objects.filter(
                    course=locked_course,
                    sign_up_status="success",
                    cancel_date__isnull=True
                ).exclude(file_status="deleted").count()
                
                if current_count >= locked_course.max_no_student:
                    messages.error(request, "非常抱歉，在您付款前該課程最後名額已被搶走！")
                    return redirect('front_web:course', hash_course)
                
                if timezone.now() > locked_course.registation_expiry_date:
                    messages.error(request, "報名已截止！")
                    return redirect('front_web:course', hash_course)

                # 確定有位子！建立 Stripe Checkout Session
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.api_version = settings.STRIPE_API_VERSION

                session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': settings.STRIPE_CURRENCY,
                            'product_data': {'name': f"{locked_course.name}-{locked_course.code}"},
                            'unit_amount': stripe_func.money_to_stripe_amount(locked_course.course_fee),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    customer_email=request.obj_student.email,
                    client_reference_id=f"course:{locked_course.id}:student:{request.obj_student.id}",
                    metadata={
                        'course_id': str(locked_course.id),
                        'student_id': str(request.obj_student.id),
                    },
                    success_url=request.build_absolute_uri(reverse('front_web:payment_successful')) + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri(reverse('front_web:payment_fail')) + f'?course_id={locked_course.id}',
                )
            
        except stripe.error.StripeError:
            messages.error(request, "未能建立付款連結，請稍後再試")
            return redirect('front_web:course', hash_course)

        return redirect(session.url, code=303)
    else:
        return render(request, "payment_fail.html", {"course_id" : course_id})

@frontweb_app_func.load_main_category
def payment_successful(request):
    # 1. 從網址列（GET 請求）撈出 Stripe 帶回來的 session_id
    session_id = request.GET.get('session_id')
    
    if not session_id:
        # 如果使用者試圖直接輸入網址偷跑進來，直接踢走！
        messages.error(request, "不合法的請求，請循正常管道付款")
        return redirect("front_web:home")
        
    try:
        # 2. 向 Stripe 總部對帳，撈出這筆交易的完整後端資料
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = settings.STRIPE_API_VERSION
        session = stripe.checkout.Session.retrieve(session_id)
        
        # 3. 嚴格檢查付款狀態是否真的為 "paid"
        if session.payment_status == "paid":
            
            try:
                signup, is_new_record = stripe_func.create_signup_from_checkout_session(session)

                if is_new_record:
                    frontweb_app_func.send_signup_success_email(request, signup)

            except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
                print("fail to create sign up")
                return HttpResponse(status=400)
            
            course = signup.course
            student = signup.student
                
            context = {
                'course_id' : course.hash_id,
                'course_list_id': course.sub_category.main_category.hash_id,
                'course_name': course.name,
                'course_code': course.code,
                'student_name': student.cn_name,
                'student_no': student.student_no,
                'amount': signup.payment_amount,
                'payment_ref': signup.payment_ref,
                'payment_date': signup.payment_date,
                'list_mc' : request.list_mc
            }
            return render(request, "payment_successful.html", context)
            
        else:
            messages.error(request, "付款尚未成功，請確認扣款狀態")
            return redirect("front_web:student_dashboard")
            
    except stripe.error.StripeError as e:
        # 萬一對帳失敗（例如黑客自己隨便編造假的 session_id 網址）
        messages.error(request, "無效的交易代碼")
        return redirect("front_web:home")
    except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
        messages.error(request, "未能確認付款資料，請聯絡本中心")
        return redirect("front_web:home")

@csrf_exempt
def stripe_webhook(request):

    print("in webhook now")

    if request.method != "POST":
        return HttpResponse(status=405)

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        return HttpResponse(status=400)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.api_version = settings.STRIPE_API_VERSION

        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] in ["checkout.session.completed", "checkout.session.async_payment_succeeded"]:
        session = event["data"]["object"]
        if session.get("payment_status") == "paid":
            try:
                stripe_func.create_signup_from_checkout_session(session)
            except (Course.DoesNotExist, Student.DoesNotExist, ValueError):
                return HttpResponse(status=400)
    #Refund handling(enable later if needed)
    # elif event["type"] == "charge.refunded":
    #     charge = event["data"]["object"]
    #     payment_intent_id = charge.get("payment_intent")
    #     refund_amount = Decimal(charge.get("amount_refunded", 0)) / Decimal("100")
        
    #     refunds = charge.get("refunds", {}).get("data", [])
    #     refund_id = refunds[0].get("id") if refunds else ""

    #     try:
    #         signup_record = SignUp.objects.get(payment_ref=payment_intent_id)         
    #         SignUpRefund.objects.create(
    #             sign_up=signup_record,
    #             refund_method="stripe",
    #             refund_amount=refund_amount,
    #             refund_ref=refund_id,
    #             created_by="System Webhook",
    #             last_updated_by="System Webhook",
    #         )
    #         print(f"退款紀錄已自動建立: 訂單 #{signup_record.id}")
            
    #     except SignUp.DoesNotExist:
    #         print(f"找不到對應的報名紀錄: {payment_intent_id}")

    return HttpResponse(status=200)

@frontweb_app_func.load_main_category
def payment_fail(request):
    course_id = request.GET.get('course_id')
    
    context = {'list_mc' : request.list_mc, "course_id" : course_id}
    return render(request, "payment_fail.html", context)
# endregion