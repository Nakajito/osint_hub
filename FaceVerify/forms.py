from django import forms
from django.core.files.uploadedfile import UploadedFile

ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/gif",
}
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

DETECTOR_CHOICES: list[tuple[str, str]] = [
    ("mtcnn", "MTCNN (preciso)"),
    ("opencv", "OpenCV (rápido)"),
]


class FaceVerifyForm(forms.Form):
    image1 = forms.ImageField(label="Imagen 1")
    image2 = forms.ImageField(label="Imagen 2")
    detector = forms.ChoiceField(choices=DETECTOR_CHOICES, initial="mtcnn")

    def _validate_image(self, f: UploadedFile) -> UploadedFile:
        if f.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Máx 10 MB.")
        if f.content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("Formato no permitido.")
        return f

    def clean_image1(self) -> UploadedFile:
        return self._validate_image(self.cleaned_data["image1"])

    def clean_image2(self) -> UploadedFile:
        return self._validate_image(self.cleaned_data["image2"])
