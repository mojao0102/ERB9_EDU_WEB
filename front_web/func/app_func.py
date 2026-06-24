from courses.models import CourseMainCategory
from administration.models import Center
from django.utils import timezone
from django.shortcuts import redirect
from functools import wraps
from students.models import Student
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from courses.func import app_func as courses_app_func

# 初始化 Django 內建的安全 Token 產生器 (會自動處理過期與防重複點擊)
token_generator = PasswordResetTokenGenerator()

# region Decorator
def load_main_category(view_func):# Decorator for load main category for nav bar
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request.list_mc = CourseMainCategory.objects.filter(is_active=True)      
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def student_access_control(require_email_verification=True):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            #Check if login
            if not request.session.get('student_id'):
                messages.error(request, "請先登入帳號")
                return redirect("front_web:student_login")

            try:#Check if student_exist
                obj_student = Student.objects.get(id=request.session.get('student_id'))
            except Student.DoesNotExist:
                messages.error(request, "帳號不存在，請聯絡中心")
                return redirect("front_web:student_login")
            
            #Check if student active
            if not obj_student.is_active:
                clear_login_session(request)
                messages.error(request, "帳號已被停權，請聯絡中心")
                return redirect("front_web:student_login")
            
            #Check if email verified
            if require_email_verification and not obj_student.is_email_verified:
                messages.warning(request, "您的電子郵件尚未驗證，請先完成驗證。")
                return redirect("front_web:student_register_pending")
            
            #For view's function to use
            request.obj_student = obj_student
            return view_func(request, *args, **kwargs)    
        return _wrapped_view
    return decorator
# endregion

# region create login session and update last login
def create_login_session(request, obj_student):
    request.session['student_id'] = obj_student.id
    request.session['student_name'] = obj_student.cn_name
    obj_student.last_login = timezone.localtime(timezone.now())
    obj_student.save()

# region clear login session
def clear_login_session(request):
    #request.session.flush()
    request.session.pop('student_id', None)
    request.session.pop('student_name', None)

# region Email verification
def verify_activation_token(student, token):
    #只負責驗證 Token 是否合法與過期，回傳 True/False
    if student is None:
        return False
    return token_generator.check_token(student, token)

def send_student_security_email(student_id, email_type, base_url): # ◄── 改傳 id 和網址字串
    try:
        # 進入 Task 後，才從資料庫撈取物件
        student = Student.objects.get(id=student_id)
        obj_center = Center.objects.first()

        uid = urlsafe_base64_encode(force_bytes(student.id))
        token = token_generator.make_token(student)

        if email_type == "activation":
            url_name = 'front_web:student_verifiy_email'
            subject = f"【{obj_center.name}】請啟用您的帳號"
            template_name = 'email_templates/student_security_email.html'
            cta_text = "啟用我的學生帳號"
            notice_text = "如果您並未註冊此帳號，請直接忽略本郵件"
        elif email_type == "reset_password":
            url_name = 'front_web:student_reset_password'
            subject = f"【{obj_center.name}】重設您的帳號密碼通知"
            template_name = 'email_templates/student_security_email.html'
            cta_text = "重設我的帳號密碼"
            notice_text = "提示：此重設連結將於 3 天後自動失效..."
        else:
            raise ValueError(f"未知的郵件類型: {email_type}")

        relative_url = reverse(url_name, kwargs={'uidb64': uid, 'token': token})
        target_url = f"{base_url.rstrip('/')}{relative_url}"

        text_content = f"親愛的 {student.cn_name} 同學，您好：\n\n請點擊下方連結：\n{target_url}\n\n{notice_text}"
        
        html_content = render_to_string(template_name, {
            'student': student,
            'target_url': target_url,
            'cta_text': cta_text,
            'notice_text': notice_text,
            'obj_center' : obj_center
        })

        msg = EmailMultiAlternatives(subject=subject, body=text_content, to=[student.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"成功發送 {email_type} 至: {student.email}")
        
    except Exception as e:
        print(f"發送失敗: {e}")

def send_signup_success_email(request, obj_signup):
    try:
        obj_center = Center.objects.first()
        obj_student = obj_signup.student
        obj_course = obj_signup.course

        pdf_bytes = courses_app_func.generate_payment_receipt_pdf(obj_signup)

        subject = f"【{obj_center.name}】報名成功確認信 - {obj_center.name}"
        target_url = request.build_absolute_uri(reverse('front_web:student_dashboard'))
        text_content = f"""親愛的 {obj_student.cn_name} 同學，您好：
        \n\n感謝您的報名！您已成功完成「{obj_course.name}」的報名與付款手續。
        \n\n交易單號：{obj_signup.payment_ref}
        \n實付金額：${obj_signup.payment_amount}
        \n\n您可以隨時登入您的學生儀表板查看課程與收據詳情：\n{target_url}\n\n{obj_center.name} 敬上"""

        html_content = render_to_string('email_templates/signup_success_email.html', {
            'student': obj_student,
            'signup': obj_signup,
            'course': obj_course,
            'target_url': target_url,
            'center': obj_center,
        })

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            to=[obj_student.email]
        )
        msg.attach_alternative(html_content, "text/html")

        # 將拿到的 PDF 掛載到 Email 上
        file_name = f"Receipt_{obj_signup.payment_ref}.pdf"
        msg.attach(file_name, pdf_bytes, 'application/pdf')

        msg.send()
        print(f"報名確認信已成功發送至: {obj_student.email}")

    except Exception as e:
        print(f"報名確認信發送失敗: {e}")
