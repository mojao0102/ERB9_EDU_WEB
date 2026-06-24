from django.utils import timezone
from django.shortcuts import render, get_object_or_404, get_list_or_404
from administration.models import Center
from courses.models import Course
from web_contents.models import News
from ..func import app_func as frontweb_app_func
from core.utils import decode_id
from django.http import Http404

# region View: Home/About
@frontweb_app_func.load_main_category
def home(request):

    current_time = timezone.localtime(timezone.now())
    
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time).order_by("-publish_date", "-created_datetime")[:3]
    #load course
    list_promote_course = Course.objects.filter(is_web_publish = True, 
                                                is_promote = True, 
                                                registation_expiry_date__gte=current_time.date(), 
                                                course_status = 'created')
    context = {
        'list_mc' : request.list_mc, 
        'list_news' : list_news, 
        'list_promote_course' : list_promote_course}  

    return render(request, "home.html", context)

@frontweb_app_func.load_main_category
def about(request):
    list_center = get_list_or_404(Center)
    context = {'list_center': list_center, 'list_mc' : request.list_mc}
    return render(request, "about.html", context)
# endregion

# region View: News
@frontweb_app_func.load_main_category
def newses(request):
    current_time = timezone.localtime(timezone.now())
    #load newses
    list_news = News.objects.filter(is_publish = True, expiry_date__gt=current_time).order_by("-publish_date", "-created_datetime")
    context = {'list_mc' : request.list_mc, "list_news" : list_news}
    return render(request, "news.html", context)

@frontweb_app_func.load_main_category
def news(request, hash_news):

    news_id = decode_id(hash_news)
    if not news_id:
        raise Http404("無效的最新消息")  

    #Get news object
    obj_news = get_object_or_404(News, id = news_id)
    context = {'list_mc' : request.list_mc, "obj_news" : obj_news}
    return render(request, "news_blog.html", context)
# endregion


