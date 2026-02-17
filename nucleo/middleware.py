"""
Middleware do OnTime.
EmpresaAtivaMiddleware: injeta a empresa do usuário no request.
"""
from django.http import Http404
from django.contrib.auth.middleware import get_user


class EmpresaAtivaMiddleware:
    """
    Injeta request.empresa a partir do usuário autenticado.
    Se o usuário não está autenticado, request.empresa = None.
    Usado pelos context_processors e pelas views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_user(request)
        if user.is_authenticated and hasattr(user, "empresa") and user.empresa:
            request.empresa = user.empresa
        else:
            request.empresa = None

        response = self.get_response(request)
        return response