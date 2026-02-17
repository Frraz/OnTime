"""
Model base abstrato para todos os models do OnTime.
Garante rastreabilidade temporal em todos os registros.
"""
from django.db import models


class ModeloBase(models.Model):
    """
    Classe base abstrata com campos de auditoria temporal.
    Todo model do sistema deve herdar desta classe.
    """
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True


class ModeloBaseComEmpresa(ModeloBase):
    """
    Extensão do ModeloBase que inclui a empresa como escopo obrigatório.
    Todo model que pertence a uma empresa deve herdar desta classe.
    Garante o isolamento multi-tenant.
    """
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_set",
        verbose_name="Empresa",
        db_index=True,
    )

    class Meta:
        abstract = True