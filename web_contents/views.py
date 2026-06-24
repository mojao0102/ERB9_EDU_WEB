from django.shortcuts import render, redirect, get_object_or_404
from .models import News
from django.contrib import messages
from django.utils import timezone
from administration.func import app_func as admin_app_func
from core.utils import decode_id
from django.http import Http404

# List
@admin_app_func.staff_access_control
def news_list(request):
    news_list = News.objects.all().order_by('-publish_date')
    return render(request, "web_contents/news_list.html", {
        "news_list" : news_list
    })

# 建立
@admin_app_func.staff_access_control
def news_create(request):
    if request.method == "POST":
        title = request.POST.get("title")
        desc = request.POST.get("desc")
        publish_date = request.POST.get("publish_date")
        expiry_date = request.POST.get("expiry_date")
        is_publish = request.POST.get("is_publish") == "on"

        news = News.objects.create(
            title=title,
            desc=desc,
            publish_date=publish_date,
            expiry_date=expiry_date,
            is_publish=is_publish,
            list_photo=request.FILES.get("list_photo"),
            photo_1=request.FILES.get("photo_1"),
            photo_2=request.FILES.get("photo_2"),
            photo_3=request.FILES.get("photo_3"),
        )
        messages.success(request, "建立成功")
        return redirect("web_contents:news_list")

    return render(request, "web_contents/news_edit.html", {"action": "create"})

# 編輯
@admin_app_func.staff_access_control
def news_edit(request, hash_news):

    news_id = decode_id(hash_news)
    if not news_id:
        raise Http404("無效的最新消息")  

    news = get_object_or_404(News, id=news_id)

    if request.method == "POST":
        news.title = request.POST.get("title")
        news.desc = request.POST.get("desc")
        news.publish_date = request.POST.get("publish_date")
        news.expiry_date = request.POST.get("expiry_date")
        news.is_publish = request.POST.get("is_publish") == "on"

        if request.FILES.get("list_photo"):
            news.list_photo = request.FILES.get("list_photo")
        if request.FILES.get("photo_1"):
            news.photo_1 = request.FILES.get("photo_1")
        if request.FILES.get("photo_2"):
            news.photo_2 = request.FILES.get("photo_2")
        if request.FILES.get("photo_3"):
            news.photo_3 = request.FILES.get("photo_3")

        news.save()
        messages.success(request, "更新成功")
        return redirect("web_contents:news_list")

    return render(request, "web_contents/news_edit.html", {
        "news": news,
        "action": "edit"
    })

# 刪除
@admin_app_func.staff_access_control
def news_delete(request, news_id):
    news = get_object_or_404(News, id=news_id)
    news.delete()
    messages.success(request, "刪除成功")
    return redirect("web_contents:news_list")