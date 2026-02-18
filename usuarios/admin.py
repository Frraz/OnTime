# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, PapelUsuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "empresa",
        "papel",
        "vinculo",
        "ativo",
    )
    list_filter = ("papel", "vinculo", "ativo", "is_staff", "is_superuser", "empresa")
    search_fields = ("username", "email", "first_name", "last_name", "matricula")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Informações Pessoais",
            {"fields": ("first_name", "last_name", "email")},
        ),
        (
            "Vínculo com Empresa",
            {
                "fields": (
                    "empresa",
                    "papel",
                    "vinculo",
                    "matricula",
                )
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "ativo",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Datas Importantes",
            {"fields": ("last_login", "date_joined", "criado_em", "atualizado_em")},
        ),
    )
    readonly_fields = ("criado_em", "atualizado_em", "last_login", "date_joined")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "empresa",
                    "papel",
                    "vinculo",
                ),
            },
        ),
    )

    def _eh_superusuario_real(self, user):
        """
        Considera superusuário quem tem is_superuser=True (Django nativo)
        OU papel=SUPERUSUARIO. Isso garante compatibilidade com usuários
        criados via createsuperuser (que não preenchem o campo 'papel').
        """
        return user.is_superuser or user.papel == PapelUsuario.SUPERUSUARIO

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Superusuários veem todos, com ou sem empresa
        if self._eh_superusuario_real(request.user):
            return qs

        # Administradores veem apenas usuários da sua empresa
        if request.user.papel == PapelUsuario.ADMINISTRADOR and request.user.empresa:
            return qs.filter(empresa=request.user.empresa)

        # Demais não acessam
        return qs.none()

    def save_model(self, request, obj, form, change):
        """
        Sincroniza papel <-> flags Django (is_staff / is_superuser).

        Regra de prioridade:
        - Se is_superuser=True foi marcado manualmente, eleva o papel para SUPERUSUARIO.
        - Caso contrário, o papel é quem manda e ajusta as flags.

        Isso evita inconsistência entre usuários criados via admin e via createsuperuser.
        """
        if obj.is_superuser and obj.papel != PapelUsuario.SUPERUSUARIO:
            # Usuário criado via createsuperuser ou promovido manualmente:
            # alinha o papel ao is_superuser do Django.
            obj.papel = PapelUsuario.SUPERUSUARIO

        # A partir daqui o papel é a fonte da verdade
        if obj.papel == PapelUsuario.SUPERUSUARIO:
            obj.is_staff = True
            obj.is_superuser = True
        elif obj.papel == PapelUsuario.ADMINISTRADOR:
            obj.is_staff = True
            obj.is_superuser = False
        else:  # COLABORADOR
            obj.is_staff = False
            obj.is_superuser = False

        super().save_model(request, obj, form, change)