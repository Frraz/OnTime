from django.contrib import admin
from .models import RegistroPonto


@admin.register(RegistroPonto)
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "tipo",
        "data_hora",
        "origem",
        "status",
        "empresa",
    )
    list_filter = ("tipo", "origem", "status", "data_hora", "empresa")
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
    )
    readonly_fields = (
        "criado_em",
        "atualizado_em",
        "empresa",
        "usuario",
        "tipo",
        "data_hora",
        "origem",
        "substitui",
        "registrado_por",
    )
    date_hierarchy = "data_hora"

    fieldsets = (
        (
            "Informações do Registro",
            {
                "fields": (
                    "empresa",
                    "usuario",
                    "tipo",
                    "data_hora",
                    "origem",
                    "status",
                )
            },
        ),
        (
            "Rastreabilidade",
            {
                "fields": (
                    "substitui",
                    "registrado_por",
                    "observacao",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": ("criado_em", "atualizado_em"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        # Nunca permitir criar registros pelo admin
        return False

    def has_change_permission(self, request, obj=None):
        # Permitir apenas alterar o status (para cancelamento)
        return request.user.eh_administrador

    def has_delete_permission(self, request, obj=None):
        # Nunca permitir deletar registros
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.papel == "SUPERUSUARIO":
            return qs
        return qs.filter(empresa=request.user.empresa)