from django.shortcuts import render
from .forms import GenerateForm, VerifyForm
import hashlib


def index(request):
    gen_result = None
    gen_form = GenerateForm(request.POST or None, request.FILES or None)
    verify_form = VerifyForm()

    if request.method == "POST" and "generate" in request.POST:
        if gen_form.is_valid():
            data = gen_form.cleaned_data
            algo = data["algorithm"]
            uploaded = request.FILES.get("file")
            h = hashlib.new(algo)
            if uploaded:
                for chunk in uploaded.chunks():
                    h.update(chunk)
            else:
                text = data.get("text") or ""
                h.update(text.encode("utf-8"))
            gen_result = h.hexdigest()

    return render(
        request,
        "hash_tool/form.html",
        {"gen_form": gen_form, "gen_result": gen_result, "verify_form": verify_form},
    )


def verify(request):
    computed = None
    match = None
    if request.method == "POST":
        form = VerifyForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            data = form.cleaned_data
            algo = data["algorithm"]
            expected = data["hash_value"].strip().lower()
            uploaded = request.FILES.get("file")
            h = hashlib.new(algo)
            if uploaded:
                for chunk in uploaded.chunks():
                    h.update(chunk)
            else:
                text = data.get("text") or ""
                h.update(text.encode("utf-8"))
            computed = h.hexdigest()
            match = computed == expected

    return render(
        request,
        "hash_tool/result.html",
        {
            "computed": computed,
            "expected": expected if "expected" in locals() else None,
            "match": match,
        },
    )
