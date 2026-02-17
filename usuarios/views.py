"""Views do domínio Usuários."""
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy


class LoginView(BaseLoginView):
    """View customizada de login."""
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy("jornada:painel")
    
    def form_invalid(self, form):
        messages.error(self.request, "Usuário ou senha inválidos.")
        return super().form_invalid(form)


@login_required
def logout_view(request):
    """Logout do usuário."""
    logout(request)
    messages.success(request, "Você saiu do sistema com sucesso.")
    return redirect("usuarios:login")


@login_required
def perfil_view(request):
    """Perfil do usuário logado."""
    return render(request, "usuarios/perfil.html", {
        "usuario": request.user,
    })