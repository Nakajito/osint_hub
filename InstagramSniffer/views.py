import logging

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from .forms import InstagramUsernameForm, InstagramPostUrlForm
from .services import fetch_collaborated_posts, fetch_media_info

logger = logging.getLogger(__name__)


def search_username(request):
    if request.method == "POST":
        form = InstagramUsernameForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            try:
                result = fetch_collaborated_posts(username)
                if result["success"]:
                    request.session["insta_sniffer_results"] = result
                    request.session["insta_sniffer_username"] = username
                    return redirect(reverse("instasniffer:results"))
                else:
                    messages.error(request, result["error"])
            except Exception as e:
                logger.exception("Error en Instagram Sniffer: %s", e)
                messages.error(request, f"Error inesperado: {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, str(err))
    else:
        form = InstagramUsernameForm()

    return render(request, "instasniffer/search.html", {"form": form})


def show_results(request):
    result = request.session.get("insta_sniffer_results", {})
    username = request.session.get("insta_sniffer_username", "-")

    posts = result.get("posts", [])
    is_private = result.get("is_private", False)

    return render(
        request,
        "instasniffer/results.html",
        {
            "posts": posts,
            "username": username,
            "is_private": is_private,
            "post_count": len(posts),
        },
    )


def search_media(request):
    if request.method == "POST":
        form = InstagramPostUrlForm(request.POST)
        if form.is_valid():
            post_url = form.cleaned_data["post_url"]
            try:
                result = fetch_media_info(post_url)
                if result["success"]:
                    request.session["insta_media_result"] = result
                    return redirect(reverse("instasniffer:media_results"))
                else:
                    messages.error(request, result["error"])
            except Exception as e:
                logger.exception("Error en Instagram Media: %s", e)
                messages.error(request, f"Error inesperado: {e}")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, str(err))
    else:
        form = InstagramPostUrlForm()

    return render(request, "instasniffer/media_search.html", {"form": form})


def show_media_results(request):
    result = request.session.get("insta_media_result", {})

    return render(
        request,
        "instasniffer/media_results.html",
        {
            "media_url": result.get("media_url", ""),
            "is_video": result.get("is_video", False),
            "filename": result.get("filename", ""),
            "success": result.get("success", False),
        },
    )
