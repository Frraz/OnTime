"""
Models do domínio Empresas.
Company é o escopo raiz do sistema multi-tenant.
"""
from django.db import models
from nucleo.models import ModeloBase


class Empresa(ModeloBase):
    """
    Representa uma empresa cliente do OnTime.
    CNPJ é único e imutável — nunca permitir alteração após criação.
    """
    razao_social = models.CharField("Razão Social", max_length=200)
    nome_fantasia = models.CharField("Nome Fantasia", max_length=200, blank=True)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    ativa = models.BooleanField("Ativa", default=True)

    # Configurações de jornada da empresa
    carga_horaria_semanal = models.DecimalField(
        "Carga Horária Semanal (horas)",
        max_digits=4,
        decimal_places=2,
        default=44.00,
    )
    tolerancia_minutos = models.PositiveSmallIntegerField(
        "Tolerância em Minutos",
        default=10,
        help_text="Minutos de tolerância para atrasos e saídas antecipadas.",
    )

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["razao_social"]

    def __str__(self):
        return self.nome_fantasia or self.razao_social

    def save(self, *args, **kwargs):
        # CNPJ não pode ser alterado após criação
        if self.pk:
            original = Empresa.objects.get(pk=self.pk)
            if original.cnpj != self.cnpj:
                raise ValueError("O CNPJ de uma empresa não pode ser alterado.")
        super().save(*args, **kwargs)