from django.utils import timezone
from django.db.models import Q, F, Count, Case, When, Value, CharField
from django.shortcuts import render, get_object_or_404
from courses.models import CourseMainCategory, CourseSubCategory, Course
from web_contents.models import News
from ..func import app_func as frontweb_app_func, stripe_func
from courses.func import app_func as course_app_func
from core.utils import decode_id
from django.http import Http404

# region View: Course/Category
@frontweb_app_func.load_main_category
def course_list(request, hash_mc):

    #hash id
    mc_id = decode_id(hash_mc)
    if not mc_id:
        raise Http404("無效的連結")

    #Get main category object by id & is_active
    obj_mc = get_object_or_404(CourseMainCategory, id = mc_id, is_active = True)

    #Get sub category list by mc_id & is_active
    list_sc = CourseSubCategory.objects.filter(main_category_id = mc_id, is_active = True).order_by("-name")

    # link up course hash id to get Sub Catergory banner
    obj_sc = None
    if hash_mc:
        try:
            real_id = decode_id(hash_mc)
            obj_sc = list_sc.get(id=real_id)
        except:
            obj_sc = list_sc.first()
    else:
        obj_sc = list_sc.first()

    context = {'list_mc' : request.list_mc, 
                "obj_mc" : obj_mc, 
                "list_sc" : list_sc,
                "obj_sc": obj_sc, # Get Sub Catergory banner
                }

    #check if is from sc button press at web page or page/mc button load
    sc_id = decode_id(request.GET['sc']) if 'sc' in request.GET else list_sc[0].id if list_sc else 0

    #Get sub category object
    if sc_id > 0 :

        context["obj_sc"] = get_object_or_404(CourseSubCategory, id = sc_id, is_active = True)

        course_filters = {
        "course_status" : "created",
        "sub_category_id" : sc_id,
        "is_web_publish" : True,
        "registation_expiry_date__gte" : timezone.now()}
        context["list_course"] = course_app_func.get_courses_with_dynamic_status(**course_filters).filter(course_dynamic_status__in=("報名中", "人數已滿"))

    return render(request, "course_list.html", context)

@frontweb_app_func.load_main_category
def course(request, hash_course):
    
    course_id = decode_id(hash_course)
    if not course_id:
        raise Http404("無效的連結")

    if request.method == "POST":
        print("POST here")
    else:#GET      
        course_filters = {"course_status" : "created", "id" : course_id, "is_web_publish" : True, "registation_expiry_date__gte" : timezone.now()}
        obj_course = course_app_func.get_courses_with_dynamic_status(**course_filters).filter(course_dynamic_status__in=("報名中", "人數已滿")).first()
        print(f"hash_id: {obj_course.hash_id}")
        if not obj_course:
            from django.http import Http404
            raise Http404("找不到該課程，或是該課程已停止報名。")

        context = {'list_mc' : request.list_mc, "obj_course" : obj_course}
        return render(request, "course.html", context)
# endregion
