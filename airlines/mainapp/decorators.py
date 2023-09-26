from functools import wraps
from django.http import HttpResponseForbidden

def admin_required(view_func): #декоратор, который помогает настроить доступ для админа (контроль доступа к представлениям)
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.RoleID.Title == "Administrator":  # Проверка, является ли пользователь администратором
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("Доступ запрещен")

    return _wrapped_view