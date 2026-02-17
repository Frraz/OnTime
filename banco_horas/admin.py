from django.contrib import admin
from .models import SaldoBancoHoras


@admin.register(SaldoBancoHoras)
class SaldoBancoHorasAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "ano",
        "semana",
        "horas_trabalhadas",
        "horas_esperadas",
        "saldo_semana",
        "saldo_acumulado",
        "fechado",
    )
    list_filter = ("fechado", "ano", "empresa")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    readonly_fields = (
        "criado_em",
        "atualizado_em",
        "horas_trabalhadas",
        "saldo_semana",
        "saldo_acumulado",
    )
    
    fieldsets = (
        (
            "Período",
            {
                "fields": ("empresa", "usuario", "ano", "semana")
            },
        ),
        (
            "Horas",
            {
                "fields": (
                    "horas_trabalhadas",
                    "horas_esperadas",
                    "saldo_semana",
                    "saldo_acumulado",
                )
            },
        ),
        (
            "Fechamento",
            {
                "fields": ("fechado", "data_fechamento", "fechado_por")
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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.papel == "SUPERUSUARIO":
            return qs
        return qs.filter(empresa=request.user.empresa)