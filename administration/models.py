from django.db import models
from core.models import AuditBaseModel

# Create your models here.

class Staff(AuditBaseModel):
    staff_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="員工編號")
    first_name = models.CharField(max_length=50, null=True, verbose_name="名字")
    last_name = models.CharField(max_length=50, null=True, verbose_name="姓氏")
    phone = models.CharField(max_length=50, null=True, verbose_name="電話")
    email = models.CharField(max_length=200, null=True, verbose_name="電子郵件")
    addr = models.CharField(max_length=200, blank=True, null=True, verbose_name="地址")
    username = models.CharField(max_length=50, blank=True, null=True, verbose_name="帳號")
    password = models.CharField(max_length=50, blank=True, null=True, verbose_name="密碼")
    remarks = models.TextField(blank=True, null=True, verbose_name="備註")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    is_admin = models.BooleanField(default=False, verbose_name="是否為管理員")
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'staff'
        verbose_name = '行政員工'
        verbose_name_plural = '行政員工'

    def __str__(self):
        return f"{self.staff_no} - {self.first_name} {self.last_name}"

    def get_email_field_name(self):
        return "email"
    
class Center(AuditBaseModel):
    name = models.CharField(max_length=200, null=True, verbose_name="中心名稱")
    addr = models.CharField(max_length=200, blank=True, null=True, verbose_name="中心地址")
    addr_desc = models.CharField(max_length=200, blank=True, null=True, verbose_name="地址描述")
    phone = models.CharField(max_length=100, blank=True, null=True, verbose_name="電話")
    fax = models.CharField(max_length=100, blank=True, null=True, verbose_name="傳真")
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name="電子郵件")
    map_url = models.TextField(blank=True, null=True, verbose_name="地圖連結")
    intro = models.TextField(blank=True, null=True, verbose_name="中心簡介")

    class Meta:
        db_table = 'center'
        verbose_name = '中心'
        verbose_name_plural = '中心'

    def __str__(self):
        return self.name or f"Center {self.id}"


class Room(AuditBaseModel):
    center = models.ForeignKey('Center', on_delete=models.CASCADE, db_column='center_id', blank=True, null=True, verbose_name="所屬中心")
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name="房間/教室名稱")
    desc = models.CharField(max_length=200, blank=True, null=True, verbose_name="描述")

    class Meta:
        db_table = 'room'
        verbose_name = '房間/教室'
        verbose_name_plural = '房間/教室'

    def __str__(self):
        return self.name or f"Room {self.id}"