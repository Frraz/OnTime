from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = (
        "razao_social",
        "nome_fantasia",
        "cnpj",
        "ativa",
        "carga_horaria_semanal",
        "criado_em",
    )
    list_filter = ("ativa", "criado_em")
    search_fields = ("razao_social", "nome_fantasia", "cnpj")
    
    fieldsets = (
        (
            "Informações Básicas",
            {
                "fields": (
                    "razao_social",
                    "nome_fantasia",
                    "cnpj",
                    "ativa",
                )
            },
        ),
        (
            "Configurações de Jornada",
            {
                "fields": (
                    "carga_horaria_semanal",
                    "tolerancia_minutos",
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

    def get_readonly_fields(self, request, obj=None):
        """
        CNPJ é readonly apenas na EDIÇÃO, não na criação.
        Criado_em e atualizado_em sempre readonly.
        """
        if obj:  # Editando
            return ("cnpj", "criado_em", "atualizado_em")
        else:  # Criando
            return ("criado_em", "atualizado_em")

    def has_delete_permission(self, request, obj=None):
        # Nunca permitir deletar empresa pelo admin
        return False