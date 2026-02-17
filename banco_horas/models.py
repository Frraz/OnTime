"""
Models do domínio Banco de Horas.
Saldo acumulativo calculado a partir dos registros de ponto.
"""
from django.db import models
from decimal import Decimal
from nucleo.models import ModeloBaseComEmpresa


class SaldoBancoHoras(ModeloBaseComEmpresa):
    """
    Saldo acumulativo de banco de horas do usuário.
    
    Este model armazena snapshots semanais do saldo.
    O saldo é calculado a partir dos registros de ponto.
    
    Positivo = horas extras a receber/compensar
    Negativo = débito de horas
    """
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="saldos_banco_horas",
        verbose_name="Usuário",
    )
    ano = models.PositiveSmallIntegerField("Ano")
    semana = models.PositiveSmallIntegerField("Semana do Ano")
    
    # Horas trabalhadas na semana
    horas_trabalhadas = models.DecimalField(
        "Horas Trabalhadas",
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    
    # Horas esperadas (carga horária da empresa)
    horas_esperadas = models.DecimalField(
        "Horas Esperadas",
        max_digits=6,
        decimal_places=2,
    )
    
    # Saldo da semana (trabalhadas - esperadas)
    saldo_semana = models.DecimalField(
        "Saldo da Semana",
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    
    # Saldo acumulado até esta semana
    saldo_acumulado = models.DecimalField(
        "Saldo Acumulado",
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    
    # Fechamento da semana
    fechado = models.BooleanField("Fechado", default=False)
    data_fechamento = models.DateTimeField("Data de Fechamento", null=True, blank=True)
    fechado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_realizados",
        verbose_name="Fechado por",
    )

    class Meta:
        verbose_name = "Saldo de Banco de Horas"
        verbose_name_plural = "Saldos de Banco de Horas"
        ordering = ["-ano", "-semana"]
        unique_together = [["empresa", "usuario", "ano", "semana"]]
        indexes = [
            models.Index(fields=["empresa", "usuario", "ano", "semana"]),
            models.Index(fields=["empresa", "fechado"]),
        ]

    def __str__(self):
        return (
            f"{self.usuario.nome_completo} - {self.ano}S{self.semana:02d} - "
            f"Saldo: {self.saldo_acumulado}h"
        )

    @property
    def saldo_formatado(self):
        """Retorna o saldo formatado com sinal."""
        if self.saldo_acumulado > 0:
            return f"+{self.saldo_acumulado}h"
        return f"{self.saldo_acumulado}h"