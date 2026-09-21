from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    message = "Xatolik yuz berdi"
    errors = {}

    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail is not None:
            message = str(detail)
        else:
            errors = response.data
            first_key = next(iter(errors), None)
            if first_key is not None:
                first_val = errors[first_key]
                if isinstance(first_val, list) and first_val:
                    message = f"{first_key}: {first_val[0]}"
                else:
                    message = f"{first_key}: {first_val}"
    elif isinstance(response.data, list):
        errors = {"non_field_errors": response.data}
        if response.data:
            message = str(response.data[0])

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
