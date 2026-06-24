from django.contrib import admin
from core.admin import ModelAdminOverride
from .models import CourseMainCategory, CourseSubCategory, Course, CourseTemplate, CourseSchedule
from django.utils.html import format_html
from django.utils.timezone import localtime
from courses.models import SignUp  # 請依據你 SignUp 真正的 app 路徑調整

@admin.register(SignUp)
class SignUpAdmin(admin.ModelAdmin):
    # 1. 列表頁面顯示的欄位
    list_display = (
        'id', 
        'student_info',     # 自訂方法：顯示學生姓名與電話
        'course_info',      # 自訂方法：顯示課程名稱與編號
        'status_badge',     # 自訂方法：漂亮的狀態標籤
        'payment_amount_display', # 格式化金額
        'payment_method', 
        'payment_ref_link', # 自訂方法：點擊可複製的收據或 Stripe 連結
        'sign_up_date_display', 
    )

    # 2. 右側篩選過濾器（快速分類）
    list_filter = (
        'sign_up_status', 
        'payment_method', 
        'file_status', 
        ('course', admin.RelatedOnlyFieldListFilter), # 只顯示目前有人報名的課程供篩選
    )

    # 3. 頂部搜尋欄（支援跨資料表搜尋學生的中文名與 Email）
    search_fields = (
        'id',
        'student__cn_name', 
        'student__en_name', 
        'student__email', 
        'course__name', 
        'course__code', 
        'payment_ref', 
        'online_payment_session'
    )

    # 4. 詳細頁面的欄位分組佈局（Fieldsets）
    fieldsets = (
        ('基本報名資訊', {
            'fields': ('student', 'course', 'sign_up_status')
        }),
        ('金流與付款細節', {
            'fields': ('payment_amount', 'payment_method', 'payment_date', 'payment_ref', 'payment_remarks')
        }),
        ('Stripe 線上串接核心（唯讀）', {
            'classes': ('collapse',), # 預設折疊收納，避免佔空間
            'description': '此區塊為系統自動對接 Stripe 產生的紀錄，請勿隨意修改。',
            'fields': ('online_payment_session',)
        }),
        ('系統稽核紀錄', {
            'fields': ('file_status', 'created_by', 'created_datetime', 'last_updated_by', 'last_updated_datetime')
        }),
    )

    # 5. 防呆機制：將自動產生的欄位與敏感金流欄位設為詳細頁面「唯讀」
    readonly_fields = (
        'created_by', 'created_datetime', 
        'last_updated_by', 'last_updated_datetime',
        'online_payment_session'
    )

    # 6. 每頁顯示筆數
    list_per_page = 25

    # 7. 自動帶入建立與更新人身分
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = f"admin:{request.user.username}"
        obj.last_updated_by = f"admin:{request.user.username}"
        super().save_model(request, obj, form, change)

    # ========== 💡 以下為優化前端外觀的自訂方法 (Custom Methods) ==========

    @admin.display(description='學生資訊')
    def student_info(self, obj):
        if obj.student:
            return format_html(
                "<strong>{}</strong><br><span style='color:#666; font-size:11px;'>{}</span>",
                obj.student.cn_name, obj.student.email
            )
        return "-"

    @admin.display(description='報讀課程')
    def course_info(self, obj):
        if obj.course:
            return format_html(
                "{}<br><span style='color:#999; font-size:11px;'>編號: {}</span>",
                obj.course.name, obj.course.code
            )
        return "-"

    @admin.display(description='狀態')
    def status_badge(self, obj):
        """ 為不同的報名狀態渲染漂亮的小圓點標籤 """
        status_colors = {
            'success': ('#dcfce7', '#166534', '報名成功'), # 綠色
            'cncel': ('#fee2e2', '#991b1b', '已被拒絕'),       # 紅色
        }
        # 取得狀態，若找不到則給予預設灰色
        bg, text, label = status_colors.get(obj.sign_up_status, ('#f3f4f6', '#374151', obj.sign_up_status))

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: bold; display: inline-block;">'
            '● {}'
            '</span>',
            bg, text, label
            )

    @admin.display(description='實付金額')
    def payment_amount_display(self, obj):
        if obj.payment_amount is not None:
            return f"${obj.payment_amount:,.2f}"
        return "$0.00"

    @admin.display(description='報名時間')
    def sign_up_date_display(self, obj):
        if obj.created_datetime:
            return localtime(obj.created_datetime)
        return obj.sign_up_date

    @admin.display(description='付款參考號')
    def payment_ref_link(self, obj):
        if not obj.payment_ref:
            return "-"
        # 萬一是用 Stripe 線上付款，可以直接做一個方便複製的代碼樣式
        return format_html(
            '<code style="background:#f1f5f9; padding:2px 6px; border-radius:4px; font-family:monospace; font-size:12px;">{}</code>',
            obj.payment_ref
        )

@admin.register(CourseMainCategory)
class CourseMainCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'created_datetime')
    search_fields = ('name',)

@admin.register(CourseSubCategory)
class CourseSubCategoryAdmin(ModelAdminOverride):
    list_display = ('name', 'main_category__name', 'created_datetime')
    search_fields = ('name', 'main_category__name')


@admin.register(CourseTemplate)
class CourseTemplateAdmin(ModelAdminOverride):
    list_display = ('name', 'sub_category__name', 'created_datetime')
    search_fields = ('name', 'sub_category__name')

@admin.register(Course)
class CourseAdmin(ModelAdminOverride):
    list_display = ('name', 'code', 'course_status', 'created_datetime')
    search_fields = ('name', 'code')

@admin.register(CourseSchedule)
class CourseScheduleAdmin(ModelAdminOverride):
    list_display = ('course__code', 'course__name', 'lesson_date', 'created_datetime')
    search_fields = ('course__code','course__name')

