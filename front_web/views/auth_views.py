from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from students.models import Student
from students.func import app_func as student_app_func
from web_contents.models import News
from ..func import app_func as frontweb_app_func


# region View: Register/EmailVerification/Login/LogOut
@frontweb_app_func.load_main_category
def student_register(request):

    if request.method == "POST":
        #Load data from POST
        username = request.POST['username']
        password = request.POST.get("password", "")
        password2 = request.POST.get("confirm_password", "")

        cn_name = request.POST['studentNameCh']
        en_name = request.POST['studentNameEn']
        dob = request.POST['studentDob']
        email = request.POST['contactEmail']
        school = request.POST['school']

        contact1Name = request.POST['contact1Name']
        contact1Phone = request.POST['contact1Phone']
        contact1Relation = request.POST['contact1Relation']

        contact2Name = request.POST['contact2Name']
        contact2Phone = request.POST['contact2Phone']
        contact2Relation = request.POST['contact2Relation']
        
        #Error Checking
        blnInputError = False

        if not password or len(password) < 6:
            messages.error(request, "密碼長度至少需要6個字元以上")
            blnInputError = True                
        if password != password2:
            messages.error(request, "密碼不匹配")
            blnInputError = True          
        elif Student.objects.filter(username=username).exists():
            messages.error(request, "帳號已存在")
            blnInputError = True          
        elif Student.objects.filter(email=email.lower()).exists():
            messages.error(request, "Email已被使用")
            blnInputError = True

        if blnInputError:
            context = {'list_mc' : request.list_mc, "input_data" : request.POST}
            return render(request, "student_register.html", context)

        #Create student
        current_time = timezone.localtime(timezone.now())
        obj_new_student = Student(student_no=student_app_func.generate_unique_student_number(),
                            cn_name=cn_name,
                            en_name=en_name,
                            dob=dob,
                            email=email,
                            #For email verification
                            is_email_verified=False,
                            contact1_name=contact1Name,
                            contact1_relationship=contact1Relation,
                            contact1_phone=contact1Phone,
                            contact2_name=contact2Name,
                            contact2_relationship=contact2Relation,
                            contact2_phone=contact2Phone,
                            school=school,
                            username=username,
                            password=password,
                            is_active=True,
                            register_date=current_time,
                            created_by="web registation",
                            last_updated_by="web registation",)
        obj_new_student.save()

        #default as logged in
        frontweb_app_func.create_login_session(request, obj_new_student)

        #Make sure last_login up to date
        obj_new_student.refresh_from_db()

        try:
            base_url = f"{request.scheme}://{request.get_host()}"
            frontweb_app_func.send_student_security_email(obj_new_student.id, "activation", base_url)
        except Exception:
            messages.warning(request, "帳號已建立，但驗證信發送失敗，請聯絡中心管理員啟用帳號")
            return redirect("front_web:student_login")
        
        messages.success(request, "註冊成功，確認郵件已寄送至您的註冊信箱。請點擊郵件中的連結驗證您的郵箱地址")
        return redirect("front_web:student_register_pending")  
    
    else: #GET
        context = {'list_mc' : request.list_mc}
        return render(request, "student_register.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control(require_email_verification=False)
def student_register_pending(request):
    context = {"email": request.obj_student.email, "list_mc": request.list_mc}
    return render(request, "student_register_pending.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control(require_email_verification=False)
def student_change_email_and_resend(request):

    obj_student = request.obj_student

    if obj_student.is_email_verified:
        messages.info(request, "您的電子郵件此前已驗證成功，無需重複驗證")
        return redirect("front_web:student_dashboard")

    if request.method == "POST":
        new_email = request.POST.get('new_email', '').strip()
        
        if not new_email:
            messages.error(request, "電子郵件欄位不可為空")
            return render(request, "student_change_email.html", {"old_email": obj_student.email, "list_mc": request.list_mc})
            
        #Check if new email addr be used by other student
        if Student.objects.filter(email=new_email).exclude(id=obj_student.id).exists():
            messages.error(request, "此電子郵件已被其他帳號註冊，請更換其他郵件")
            return render(request, "student_change_email.html", {"old_email": obj_student.email, "list_mc": request.list_mc})
            
        obj_student.email = new_email
        obj_student.save()
        
        #Send verification
        try:
            #frontweb_app_func.send_verification_email(request, obj_student, "activation")
            base_url = f"{request.scheme}://{request.get_host()}"
            frontweb_app_func.send_student_security_email(obj_student.id, "activation", base_url)
            messages.success(request, f"Email修改成功！全新的驗證信已成功寄送至：{new_email}")
        except Exception:
            messages.warning(request, "Email雖已修改，但新驗證信發送失敗，請聯絡中心管理員")
            
        #Switch to email pending
        return redirect("front_web:student_register_pending")
        
    #GET
    context={"old_email": obj_student.email, "list_mc": request.list_mc}
    return render(request, "student_change_email.html", context)

def student_verifiy_email(request, uidb64, token):
    #負責解密 uid 並檢查 Token 是否依然有效，有效則改為已驗證
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        obj_student = Student.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Student.DoesNotExist):
        obj_student = None
    # 核心安全驗證：檢查 Token 是否合法、是否過期、對象資料是否變動過
    if obj_student is not None and frontweb_app_func.verify_activation_token(obj_student, token):
        obj_student.is_email_verified = True
        #Update last_login for killing the token
        obj_student.last_login = timezone.localtime(timezone.now())
        obj_student.save()
        messages.success(request, "您的電子信箱已成功驗證！現在可以正常登入系統了")
        return redirect('front_web:student_login')
    else:
        frontweb_app_func.clear_login_session(request)
        return HttpResponse("<h3>此啟用連結已失效或過期，請重新嘗試註冊或聯絡中心</h3>")

@frontweb_app_func.load_main_category
def student_login(request):

    if request.method == "POST":
    #Load data from POST
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        try:
            obj_student = Student.objects.get(Q(username=username) & Q(password=password) & ~Q(file_status="deleted"))  

            if not obj_student.is_active:
                frontweb_app_func.clear_login_session(request)
                messages.error(request, "帳號已被停權，請聯絡中心")
                return redirect("front_web:student_login")
            else:
                frontweb_app_func.create_login_session(request, obj_student)
                messages.success(request, f"歡迎回來，{obj_student.username}")
                return redirect("front_web:home")
            
        except Student.DoesNotExist:
            frontweb_app_func.clear_login_session(request)
            messages.error(request, "帳號或密碼錯誤，請重新輸入")        
            context = {'list_mc': request.list_mc, 'input_data': request.POST}
            return render(request, "student_login.html", context)
        
        except Exception as e:
            print(f"student login error, username:{username}, error:{e}")
            messages.error(request, "系統帳號異常，請聯絡中心管理員")
            return render(request, "student_login.html", context)
        
    else:#Get
        context = {'list_mc' : request.list_mc}
        return render(request, "student_login.html", context)
    
@frontweb_app_func.load_main_category
def student_logout(request):
    if request.method == "POST":
        frontweb_app_func.clear_login_session(request)      
        messages.success(request, "你已成功登出")
        return redirect("front_web:student_login")  
    return render(request, "home.html")

@frontweb_app_func.load_main_category
def student_forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()     
        obj_student = Student.objects.filter(email=email).first()
        if obj_student:
            #frontweb_app_func.send_password_reset_email(request, obj_student, "reset_password")
            base_url = f"{request.scheme}://{request.get_host()}"
            frontweb_app_func.send_student_security_email(obj_student.id, "reset_password", base_url)
        messages.success(request, "重設驗證連結已成功寄出，請至您的電子信箱查收")
        return redirect("front_web:student_login")
    
    context = {'list_mc' : request.list_mc}
    return render(request, "student_forget_password.html", context)

@frontweb_app_func.load_main_category
def student_reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        obj_student = Student.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Student.DoesNotExist):
        obj_student = None

    # 核心安全驗證：檢查 Token 是否有效
    if obj_student is not None and frontweb_app_func.verify_activation_token(obj_student, token):
        
        if request.method == "POST":
            password = request.POST.get("password", "")
            password_confirm = request.POST.get("confirm_password", "")
            
            if not password or len(password) < 6:
                messages.error(request, "密碼長度至少需要6個字元以上")
                return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})
                
            if password != password_confirm:
                messages.error(request, "密碼不匹配")
                return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})

            obj_student.password = password
            obj_student.save()
            
            frontweb_app_func.clear_login_session(request)          
            messages.success(request, "密碼已成功更新, 請使用新密碼進行登入")
            return redirect("front_web:student_login")
        
        return render(request, "student_reset_password.html", {"uidb64": uidb64, "token": token, 'list_mc' : request.list_mc})
    else:
        return HttpResponse("<h3>該密碼重設連結已失效、過期或已被使用, 請重新申請</h3>")
# endregion

# region Edit user info/Change password
@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_edit_info(request):

    if request.method == "POST":
        cn_name = request.POST.get('studentNameCh')
        en_name = request.POST.get('studentNameEn')
        dob = request.POST.get('studentDob')
        school = request.POST.get('school')

        contact1Name = request.POST.get('contact1Name')
        contact1Phone = request.POST.get('contact1Phone')
        contact1Relation = request.POST.get('contact1Relation')

        contact2Name = request.POST.get('contact2Name')
        contact2Phone = request.POST.get('contact2Phone')
        contact2Relation = request.POST.get('contact2Relation')

        try:
            #Get student
            obj_student = Student.objects.get(id=request.session.get('student_id'))

            obj_student.cn_name=cn_name
            obj_student.en_name=en_name
            obj_student.dob=dob
            obj_student.school=school

            obj_student.contact1_name=contact1Name
            obj_student.contact1_relationship=contact1Relation
            obj_student.contact1_phone=contact1Phone

            obj_student.contact2_name=contact2Name
            obj_student.contact2_relationship=contact2Relation
            obj_student.contact2_phone=contact2Phone

            obj_student.last_updated_by=f"student_id:{obj_student.id}"

            obj_student.save()

            messages.success(request, "成功修改")
            return redirect("front_web:student_edit_info")

        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, "系統錯誤, 請聯絡中心管理員")
            context = {'list_mc' : request.list_mc, "student" : request.obj_student, "input_data" : request.POST}
            return render(request, "student_edit_info.html", context)   
    else:    
        context = {'list_mc' : request.list_mc, "student" : request.obj_student}
        return render(request, "student_edit_info.html", context)

@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_change_password(request):   

    if request.method == "POST":
        old_password = request.POST.get('old_password', "")
        new_password = request.POST.get('new_password', "")
        confirm_new_password = request.POST.get('confirm_new_password', "")

        try:
            #GEt student
            obj_student = Student.objects.get(id=request.session.get('student_id'))

            #check input
            blnInputError = False
            if old_password != obj_student.password:
                messages.error(request, "目前密碼不正確")
                blnInputError = True  
            elif not new_password or len(new_password) < 6:
                messages.error(request, "新密碼長度至少需要6個字元以上")
                blnInputError = True                
            elif new_password != confirm_new_password:
                messages.error(request, "新密碼不匹配")
                blnInputError = True          

            if blnInputError:
                context = {'list_mc' : request.list_mc, "student" : request.obj_student}
                return render(request, "student_change_password.html", context)

            obj_student.password=new_password
            obj_student.last_updated_by=f"student_id:{obj_student.id}"
            obj_student.save()

            messages.success(request, "成功修改密碼")
            return redirect("front_web:student_change_password")

        except Exception as e:
            print(f"An error occurred: {e}")
            messages.error(request, "系統錯誤, 請聯絡中心管理員")
            context = {'list_mc' : request.list_mc, "student" : request.obj_student}
            return render(request, "student_change_password.html", context)   
    else:  
        context = {'list_mc' : request.list_mc, "student" : request.obj_student}
        return render(request, "student_change_password.html", context)
# endregion