from django.db import models
from core.models import AuditBaseModel
from core.utils import encode_id

# Create your models here.
class Student(AuditBaseModel):
    student_no = models.CharField(max_length=50, unique=True, verbose_name="編號")
    cn_name = models.CharField(max_length=100, verbose_name="中文姓名")
    en_name = models.CharField(max_length=100, verbose_name="英文姓名")
    dob = models.DateField(blank=True, verbose_name="出生日期")

    email = models.EmailField(max_length=200, blank=True, verbose_name="Email")
    is_email_verified = models.BooleanField(default=False, verbose_name="Email是否已驗證?")
    
    # v04 緊急聯絡人結構
    contact1_name = models.CharField(max_length=200, blank=True, verbose_name="聯絡人1姓名")
    contact1_relationship = models.CharField(max_length=100, blank=True, verbose_name="聯絡人1關係")
    contact1_phone = models.CharField(max_length=100, verbose_name="聯絡人1電話")
    
    contact2_name = models.CharField(max_length=200, blank=True, verbose_name="聯絡人2姓名")
    contact2_relationship = models.CharField(max_length=100, blank=True, verbose_name="聯絡人2關係")
    contact2_phone = models.CharField(max_length=100, blank=True, verbose_name="聯絡人2電話")
    
    school = models.CharField(max_length=200, blank=True, verbose_name="學校")

    remarks = models.TextField(blank=True, verbose_name="備註")

    username = models.CharField(max_length=50, unique=True, verbose_name="登入帳號")
    password = models.CharField(max_length=50, verbose_name="密碼")

    is_active = models.BooleanField(default=True, verbose_name="是否啟用?")
    register_date = models.DateTimeField(blank=True, verbose_name="註冊日期")
    expiry_date = models.DateTimeField(blank=True, null=True, verbose_name="帳號效期截止日")
    
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'student'
        verbose_name = "學生資料"
        verbose_name_plural = "學生資料"
        ordering = ['register_date', 'created_datetime']

    def __str__(self):
        return f"{self.cn_name} ({self.en_name}) - {self.student_no}"
    
    def get_email_field_name(self):
        return "email"
    
    @property
    def hash_id(self):
        return encode_id(self.id)
    

