from django.db import models
from core.models import AuditBaseModel
from core.utils import encode_id

# Create your models here.
from django.db import models

class News(AuditBaseModel):

    title = models.CharField(max_length=200, verbose_name="標題")
    publish_date = models.DateTimeField(verbose_name="發布日期")
    expiry_date = models.DateTimeField(blank=True, verbose_name="到期日期")
    is_publish = models.BooleanField(default=False, verbose_name="是否發布")
    desc = models.TextField(blank=True, verbose_name="內文描述")

    list_photo = models.ImageField(upload_to='news/%Y/%m/%d/', blank=True, verbose_name="列表展示圖片")
    photo_1 = models.ImageField(upload_to='news/%Y/%m/%d/', blank=True, verbose_name="圖片1")
    photo_2 = models.ImageField(upload_to='news/%Y/%m/%d/', blank=True, verbose_name="圖片2")
    photo_3 = models.ImageField(upload_to='news/%Y/%m/%d/', blank=True, verbose_name="圖片3")

    class Meta:
        db_table = 'news'
        verbose_name = '最新消息'
        verbose_name_plural = '最新消息'

    def __str__(self):
        return self.title or f"News {self.id}"

    @property
    def hash_id(self):
        return encode_id(self.id)

# class Inquiry(models.Model):
#     id = models.AutoField(primary_key=True)
#     title = models.CharField(max_length=200, blank=True, verbose_name="諮詢標題")
#     publish_date = models.DateTimeField(blank=True, verbose_name="發布日期")
#     is_publish = models.BooleanField(default=True, verbose_name="是否發布")
#     desc = models.TextField(blank=True, verbose_name="諮詢描述")
#     list_photo = models.CharField(max_length=100, blank=True, verbose_name="列表圖片路徑")
#     photo_1 = models.CharField(max_length=100, blank=True, verbose_name="圖片 1 路徑")
#     photo_2 = models.CharField(max_length=100, blank=True, verbose_name="圖片 2 路徑")
#     photo_3 = models.CharField(max_length=100, blank=True, verbose_name="圖片 3 路徑")
#     file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
#     created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
#     created_datetime = models.DateTimeField(blank=True, verbose_name="建立時間")
#     last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
#     last_updated_datetime = models.DateTimeField(blank=True, verbose_name="最後更新時間")

#     class Meta:
#         db_table = 'inquiry'
#         verbose_name = '諮詢管理 (暫未使用)'
#         verbose_name_plural = '諮詢管理 (暫未使用)'

#     def __str__(self):
#         return self.title or f"Inquiry {self.id}"