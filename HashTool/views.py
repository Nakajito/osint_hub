import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import GenerateForm, VerifyForm


def calculate_hash(algo, file=None, text=None):
    """Función auxiliar para calcular el hash de un archivo o texto."""
    h = hashlib.new(algo)
    if file:
        for chunk in file.chunks():
            h.update(chunk)
    elif text:
        h.update(text.encode("utf-8"))
    return h.hexdigest()


def index(request):
    gen_result = None
    # Inicializamos ambos formularios para que el template siempre los tenga
    gen_form = GenerateForm(request.POST or None, request.FILES or None)
    verify_form = VerifyForm()

    if request.method == "POST" and "generate" in request.POST:
        if gen_form.is_valid():
            data = gen_form.cleaned_data
            gen_result = calculate_hash(
                algo=data["algorithm"],
                file=request.FILES.get("file"),
                text=data.get("text"),
            )
            messages.info(request, "Hash generado con éxito.")

    return render(
        request,
        "hash_tool/form.html",
        {"gen_form": gen_form, "gen_result": gen_result, "verify_form": verify_form},
    )


def verify(request):
    if request.method == "POST":
        form = VerifyForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            expected = data["hash_value"].strip().lower()

            computed = calculate_hash(
                algo=data["algorithm"],
                file=request.FILES.get("file"),
                text=data.get("text"),
            )

            if computed == expected:
                messages.success(
                    request, f"¡Verificación exitosa! El hash coincide: {computed}"
                )
            else:
                messages.error(
                    request,
                    "Error de integridad: El hash calculado no coincide con el proporcionado.",
                )
        else:
            messages.warning(
                request,
                "Por favor, revisa los datos ingresados en el formulario de verificación.",
            )

    # Redireccionamos al index para mostrar el mensaje y mantener la UI limpia
    return redirect("HashTool:index")
