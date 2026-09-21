from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE_MB = 20
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}


def validate_file_size(file):
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f"Fayl hajmi {MAX_UPLOAD_SIZE_MB}MB dan oshmasligi kerak.")


def validate_document_extension(file):
    name = file.name.lower()
    if not any(name.endswith(ext) for ext in ALLOWED_DOCUMENT_EXTENSIONS):
        raise ValidationError("Ruxsat etilmagan fayl turi.")
