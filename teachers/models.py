from django.db import models
from core.models import AuditBaseModel
from core.utils import encode_id #For hash id

# Create your models here.
from django.db import models

class Teacher(AuditBaseModel):
    teacher_no = models.CharField(max_length=50, blank=True, verbose_name="導師編號")
    title = models.CharField(max_length=50, blank=True, verbose_name="稱謂/職稱")
    first_name = models.CharField(max_length=50, verbose_name="名字")
    last_name = models.CharField(max_length=50, verbose_name="姓氏")
    phone = models.CharField(max_length=50, verbose_name="電話")
    email = models.CharField(max_length=200, verbose_name="電子郵件")
    addr = models.CharField(max_length=200, blank=True, verbose_name="地址")
    dob = models.DateField(null=True, blank=True, verbose_name="出生日期")
    username = models.CharField(max_length=50, blank=True, verbose_name="帳號")
    password = models.CharField(max_length=50, blank=True, verbose_name="密碼")
    remarks = models.TextField(blank=True, verbose_name="備註")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")

    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'teacher'
        verbose_name = '導師'
        verbose_name_plural = '導師'

    def __str__(self):
        return f"{self.teacher_no} - {self.first_name} {self.last_name}"
    
    def get_email_field_name(self):
        return "email"
    
    @property
    def hash_id(self):
        return encode_id(self.id)