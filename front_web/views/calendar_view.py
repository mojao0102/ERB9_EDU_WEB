from django.utils import timezone
from django.db.models import F, Prefetch
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta

from courses.models import Course, CourseSchedule, SignUp
from students.models import Student
from ..func import app_func as frontweb_app_func

# region View: Student Calendar
@frontweb_app_func.load_main_category
@frontweb_app_func.student_access_control()
def student_calendar_page(request):
    context = {
        'list_mc': request.list_mc,
    }
    return render(request, "student_course_calendar.html", context)


# 重點：用 method_decorator 包裝權限裝飾器給 class view 使用
@method_decorator(frontweb_app_func.student_access_control(), name='get')
class StudentCalendarEventAPI(View):
    def get(self, request):
        student_id = request.session.get('student_id')
        print("=== 當前登入學生ID ===", student_id)

        # 1. 撈有效報名 (與原邏輯相同)
        valid_signups = SignUp.objects.filter(
            student_id=student_id,
            sign_up_status='success',
            cancel_date__isnull=True
        ).exclude(file_status='deleted').select_related("course")
        
        list_course_id = [signup.course.id for signup in valid_signups]
        if not list_course_id:
            print("沒有任何有效報名課程")
            return JsonResponse([], safe=False) # 配合 FullCalendar 預設接收陣列格式

        # 2. 撈對應課程，並優化 Prefetch 排期表
        student_courses = Course.objects.filter(
            id__in=list_course_id,
            course_status='created',
        ).exclude(file_status='deleted').prefetch_related(
            # 排除已被軟刪除的排期，並依照日期與時間排序，讓資料更乾淨
            Prefetch("courseschedule_set", queryset=CourseSchedule.objects.exclude(file_status='deleted').order_by('lesson_date', 'start_time'))
        )
        print("=== 撈到學生課程數量 ===", student_courses.count())

        events = []
        for course in student_courses:
            course_center_name = course.center.name if course.center else "未設定分校"
            schedule_list = course.courseschedule_set.all()
            
            for schedule in schedule_list:
                if not schedule.lesson_date:
                    continue
                
                actual_date = schedule.lesson_date.date()
                full_start_dt = datetime.combine(actual_date, schedule.start_time)
                full_end_dt = datetime.combine(actual_date, schedule.end_time)

                # 先把時間轉成漂亮的 24 小時制字串 (例如 "16:00")
                start_time_str = schedule.start_time.strftime("%H:%M")
                end_time_str = schedule.end_time.strftime("%H:%M")

                event_item = {
                    # 調整日曆標題：只顯示 "16:00 課程名稱"
                    "title": f"{start_time_str} {course.name}",
                    
                    "start": full_start_dt.isoformat(),
                    "end": full_end_dt.isoformat(),
                    
                    # 調整懸浮提示框：加入精準的開始與結束時間
                    "description": (
                        f"課程編號：{course.code}\n"
                        f"上課時間：{start_time_str} - {end_time_str}\n"  # 👈 新增這一行
                        f"上課分校：{course_center_name}\n"
                        f"課堂主題：{schedule.lesson_title if schedule.lesson_title else '未命名課堂'}\n" # 把主題移到這裡
                        f"備註：{schedule.remarks if schedule.remarks else '無'}"
                    ),
                    "backgroundColor": "#165DFF",
                    "textColor": "#ffffff"
                }
                events.append(event_item)
                print(f"生成事件：{full_start_dt} {event_item['title']}")

        print(f"最終返回行事曆事件總數：{len(events)}")
        return JsonResponse(events, safe=False)
# endregion