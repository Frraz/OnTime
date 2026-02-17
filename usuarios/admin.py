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

    def get_queryset(self, request):
        """
        Filtro de queryset baseado no papel do usuário logado.
        
        IMPORTANTE: Superusuários veem TODOS, incluindo usuários sem empresa.
        Administradores veem apenas da sua empresa.
        """
        qs = super().get_queryset(request)
        
        # Superusuários veem todos os usuários (inclusive sem empresa)
        if request.user.papel == PapelUsuario.SUPERUSUARIO:
            return qs
        
        # Administradores veem apenas usuários da sua empresa
        if request.user.papel == PapelUsuario.ADMINISTRADOR and request.user.empresa:
            return qs.filter(empresa=request.user.empresa)
        
        # Colaboradores não acessam admin de usuários
        return qs.none()

    def save_model(self, request, obj, form, change):
        """
        Ao salvar, ajusta is_staff e is_superuser baseado no papel.
        """
        # Sincronizar papel com permissões Django
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