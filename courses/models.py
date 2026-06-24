from django.db import models
from core.models import AuditBaseModel
from colorfield.fields import ColorField
from .choices import course_status
from administration.models import Center, Room, Staff
from teachers.models import Teacher
from students.models import Student
from django.utils import timezone
from core.utils import encode_id #For hash id
from django.db.models import Sum

class CourseMainCategory(AuditBaseModel):

    name = models.CharField(max_length=50, verbose_name="主類別名稱")
    short_name = models.CharField(max_length=50, verbose_name="簡稱")
    desc = models.TextField(blank=True, verbose_name="描述")
    main_cat_code = models.CharField(max_length=50, blank=True, verbose_name="命名編號")
    nav_icon = models.CharField(max_length=100, verbose_name="Icon(FontAwesome Icon Class)", help_text="例如: fa-baby", blank=True, null=True)
    home_photo = models.ImageField(upload_to='main_category/%Y/%m/%d/', blank=True, null=True, verbose_name="首頁圖片")
    list_photo = models.ImageField(upload_to='sub_category/%Y/%m/%d/', blank=True, null=True, verbose_name="課程列表圖片")
    theme_color = ColorField(default="", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="是否可在用/顯示")

    class Meta:
        db_table = 'course_main_category'
        verbose_name = '課程主類別'
        verbose_name_plural = '課程主類別'

    def __str__(self):
        return self.name or f"MainCategory {self.id}"
    
    @property
    def hash_id(self):
        return encode_id(self.id)


class CourseSubCategory(AuditBaseModel):
    main_category = models.ForeignKey(CourseMainCategory, on_delete=models.CASCADE, db_column='main_category_id', verbose_name="所屬主類別")
    name = models.CharField(max_length=50, verbose_name="子類別名稱")
    short_name = models.CharField(max_length=50, verbose_name="簡稱")
    desc = models.TextField(blank=True, verbose_name="描述")
    sub_cat_code = models.CharField(max_length=50, blank=True, verbose_name="命名編號")
    list_photo = models.ImageField(upload_to='sub_category/%Y/%m/%d/', blank=True, verbose_name="課程列表圖片")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="是否可在用/顯示")

    class Meta:
        db_table = 'course_sub_category'
        verbose_name = '課程子類別'
        verbose_name_plural = '課程子類別'

    def __str__(self):
        return self.name or f"SubCategory {self.id}"
    
    @property
    def hash_id(self):
        return encode_id(self.id)
    
class CourseTemplate(AuditBaseModel):
    teacher = models.ForeignKey(Teacher, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='templates', verbose_name="老師")
    sub_category = models.ForeignKey(CourseSubCategory, on_delete=models.DO_NOTHING, blank=True,  verbose_name="分類")   
    name = models.CharField(max_length=50, verbose_name="課程名稱")
    content = models.TextField(blank=True, verbose_name="課程介紹")
    
    # 彈性擴充特徵欄位
    feature_1 = models.CharField(max_length=200, blank=True, verbose_name="特徵 1")
    feature_2 = models.CharField(max_length=200, blank=True, verbose_name="特徵 2")
    feature_3 = models.CharField(max_length=200, blank=True, verbose_name="特徵 3")
    feature_4 = models.CharField(max_length=200, blank=True, verbose_name="特徵 4")
    feature_5 = models.CharField(max_length=200, blank=True, verbose_name="特徵 5")
    feature_6 = models.CharField(max_length=200, blank=True, verbose_name="特徵 6")
    feature_7 = models.CharField(max_length=200, blank=True, verbose_name="特徵 7")
    feature_8 = models.CharField(max_length=200, blank=True, verbose_name="特徵 8")
    
    total_lessons = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="總堂數")
    hours_per_lesson = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="每堂時數")
    total_hours = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="總時數")
    course_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, verbose_name="預設學費")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用", help_text="控制此範本是否可在開課時被選用")

    class Meta:
        db_table = 'course_template'
        verbose_name = "課程範本"
        verbose_name_plural = "課程範本"
        ordering = ['-id']

    def __str__(self):
        return self.name
    
    @property
    def hash_id(self):
        return encode_id(self.id)

class Course(AuditBaseModel):
    template = models.ForeignKey(CourseTemplate, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="範本")
    sub_category = models.ForeignKey(CourseSubCategory, on_delete=models.DO_NOTHING, verbose_name="分類")
    teacher = models.ForeignKey(Teacher, on_delete=models.DO_NOTHING, verbose_name="老師")
    center = models.ForeignKey(Center, on_delete=models.DO_NOTHING,  null=True, blank=True, verbose_name="上課分校/中心")
    default_room = models.ForeignKey(Room, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="預設上課教室")
    
    code = models.CharField(max_length=50, verbose_name="課程編號", help_text="例如：PY-2026-001")
    name = models.CharField(max_length=50, verbose_name="課程名稱")
    photo = models.ImageField(upload_to='course/%Y/%m/%d/', blank=True, verbose_name="首頁展示圖片")
    content = models.TextField(blank=True, verbose_name="課程介紹")
    
    feature_1 = models.CharField(max_length=200, blank=True, verbose_name="詳情 1")
    feature_2 = models.CharField(max_length=200, blank=True, verbose_name="詳情 2")
    feature_3 = models.CharField(max_length=200, blank=True, verbose_name="詳情 3")
    feature_4 = models.CharField(max_length=200, blank=True, verbose_name="詳情 4")
    feature_5 = models.CharField(max_length=200, blank=True, verbose_name="詳情 5")
    feature_6 = models.CharField(max_length=200, blank=True, verbose_name="詳情 6")
    feature_7 = models.CharField(max_length=200, blank=True, verbose_name="詳情 7")
    feature_8 = models.CharField(max_length=200, blank=True, verbose_name="詳情 8")
    
    age_group = models.CharField(max_length=200, blank=True, verbose_name="對象")

    total_lessons = models.IntegerField(verbose_name="總上課堂數")
    hours_per_lesson = models.DecimalField(max_digits=5, decimal_places=1, blank=True, verbose_name="每堂上課時數")
    
    # 日期與時間 (v04 核心欄位：供前端扁平表單輸入)
    period_from = models.DateField(verbose_name="開始日期")
    period_to = models.DateField(verbose_name="結束日期")
    time_from = models.TimeField(blank=True, verbose_name="上課開始時間", help_text="格式如 14:00") 
    time_to = models.TimeField(blank=True, verbose_name="上課結束時間", help_text="格式如 16:00")

    is_mon = models.BooleanField(default=False, verbose_name="星期一")
    is_tue = models.BooleanField(default=False, verbose_name="星期二")
    is_wed = models.BooleanField(default=False, verbose_name="星期三")
    is_thu = models.BooleanField(default=False, verbose_name="星期四")
    is_fri = models.BooleanField(default=False, verbose_name="星期五")
    is_sat = models.BooleanField(default=False, verbose_name="星期六")
    is_sun = models.BooleanField(default=False, verbose_name="星期日")

    # lesson_weekday_pattern = models.CharField(max_length=200, blank=True, verbose_name="課程日期安排模式", help_text="格式如 逢星期六")

    course_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="學費") 
    max_no_student = models.IntegerField(verbose_name="人數上限")
    registation_expiry_date = models.DateTimeField(blank=True, verbose_name="截止時間")
    is_promote = models.BooleanField(default=False, verbose_name="是是否在首頁推薦?")
    is_web_publish = models.BooleanField(default=False, verbose_name="是否公開發布?")
    course_status = models.CharField(max_length=50, choices=course_status.items(), default="", verbose_name="課程狀態")

    class Meta:
        db_table = 'course'
        verbose_name = "課程"
        verbose_name_plural = "課程"
        ordering = ['-id']

    def __str__(self):
        return f"[{self.code}] {self.name}"
    
    @property
    def hash_id(self):
        return encode_id(self.id)
    
    @property
    def lesson_weekday_pattern(self):
        list_wd = []
        if self.is_mon:
            list_wd.append("一")
        if self.is_tue:
            list_wd.append("二")
        if self.is_wed:
            list_wd.append("三")
        if self.is_thu:
            list_wd.append("四")
        if self.is_fri:
            list_wd.append("五")
        if self.is_sat:
            list_wd.append("六")
        if self.is_sun:
            list_wd.append("日")
        if list_wd:     
            return "逢星期" + ", ".join(list_wd)
        else:
            return ""
        
    @property
    def lesson_weekday(self):
        list_wd = []
        if self.is_mon:
            list_wd.append(1)
        if self.is_tue:
            list_wd.append(2)
        if self.is_wed:
            list_wd.append(3)
        if self.is_thu:
            list_wd.append(4)
        if self.is_fri:
            list_wd.append(5)
        if self.is_sat:
            list_wd.append(6)
        if self.is_sun:
            list_wd.append(7)
        return list_wd


class CourseSchedule(AuditBaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="課程")
    lesson_date = models.DateTimeField(blank=True, null=True, verbose_name="上課日期")
    start_time = models.TimeField(verbose_name="開始時間")
    end_time = models.TimeField(verbose_name="結束時間")

    lesson_title = models.CharField(max_length=200, blank=True, verbose_name="課堂標題")
    lesson_content = models.TextField(blank=True, verbose_name="課堂內容")
    remarks = models.TextField(blank=True, verbose_name="備註")

    class Meta:
        db_table = 'course_schedule'
        verbose_name = "課程排班表"
        verbose_name_plural = "課程排班表"
        ordering = ['course', 'lesson_date', 'start_time']

    @property
    def hash_id(self):
        return encode_id(self.id)

class SignUp(AuditBaseModel):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, verbose_name="學生")
    course = models.ForeignKey(Course, on_delete=models.DO_NOTHING, verbose_name="課程")
    sign_up_status = models.CharField(max_length=50, blank=True, verbose_name="狀態")
    sign_up_date = models.DateTimeField(default=timezone.now, verbose_name="報名時間")
    
    cancel_date = models.DateTimeField(blank=True, null=True, verbose_name="取消時間")
    cancel_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="取消者")
    cancel_reason = models.CharField(max_length=200, blank=True, verbose_name="取消原因")

    payment_date = models.DateTimeField(default=timezone.now, verbose_name="付款時間")
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, verbose_name="付款金額")
    payment_method = models.CharField(max_length=50, blank=True, verbose_name="付款方式")#Stripe or cash(by staff)
    payment_ref = models.CharField(max_length=255, blank=True, verbose_name="付款參考")
    online_payment_session = models.CharField(max_length=255, blank=True, verbose_name="Stripe Session")
    payment_remarks = models.CharField(max_length=200, blank=True, verbose_name="付款備註")

    class Meta:
        db_table = 'sign_up'
        verbose_name = "課程報名"
        verbose_name_plural = "課程報名"
        ordering = ['-id']

    def __str__(self):
        return f"{self.student} - {self.course}"
    
    @property
    def hash_id(self):
        return encode_id(self.id)
    
    # @property
    # def total_refund_amount(self):
    #     result = self.signuprefund_set.exclude(file_status='deleted').aggregate(total=Sum('refund_amount'))['total']
    #     return result or 0
    
class SignUpRefund(AuditBaseModel):
    sign_up = models.ForeignKey(SignUp, on_delete=models.CASCADE, verbose_name="報名紀錄")
    refund_date = models.DateTimeField(default=timezone.now, verbose_name="退款日期")
    refund_method = models.CharField(max_length=100, blank=True, verbose_name="退款方式")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="退款金額")
    refund_ref = models.CharField(max_length=255, blank=True, verbose_name="退款參考")
    refund_reason = models.CharField(max_length=200, blank=True, verbose_name="退款原因")
    refund_by = models.ForeignKey(Staff, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="處理人")

    class Meta:
        db_table = 'sign_up_refund'
        verbose_name = "報名退款"
        verbose_name_plural = "報名退款"
        ordering = ['-id']

    def __str__(self):
        return f"Refund for SignUp #{self.sign_up.id}"    
    
    @property
    def hash_id(self):
        return encode_id(self.id)
        