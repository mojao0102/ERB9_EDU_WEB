from django.db import models

# Create your models here.
class AuditBaseModel(models.Model):
    file_status = models.CharField(max_length=100, blank=True, verbose_name="檔案狀態")
    created_by = models.CharField(max_length=100, blank=True, verbose_name="建立者")
    created_datetime = models.DateTimeField(auto_now_add=True, verbose_name="建立日期時間")
    last_updated_by = models.CharField(max_length=100, blank=True, verbose_name="最後更新者")
    last_updated_datetime = models.DateTimeField(auto_now=True, verbose_name="最後更新日期時間")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.file_status = 'created'
            
        elif self.file_status not in ('deleted',): 
            self.file_status = 'updated'          
        super().save(*args, **kwargs)
