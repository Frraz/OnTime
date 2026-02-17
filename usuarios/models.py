"""
Model de usuário customizado do OnTime.
Estende AbstractUser com papel, vínculo e empresa.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class PapelUsuario(models.TextChoices):
    COLABORADOR = "COLABORADOR", "Colaborador"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    SUPERUSUARIO = "SUPERUSUARIO", "Superusuário"


class VinculoUsuario(models.TextChoices):
    INTERNO = "INTERNO", "Interno"
    EXTERNO = "EXTERNO", "Externo"
    CONFIANCA = "CONFIANCA", "Confiança"


class Usuario(AbstractUser):
    """
    Usuário do sistema OnTime.
    Sempre associado a uma empresa (exceto superusuários do sistema).
    """
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="usuarios",
        verbose_name="Empresa",
        null=True,
        blank=True,
    )
    papel = models.CharField(
        "Papel",
        max_length=20,
        choices=PapelUsuario.choices,
        default=PapelUsuario.COLABORADOR,
    )
    vinculo = models.CharField(
        "Vínculo",
        max_length=20,
        choices=VinculoUsuario.choices,
        default=VinculoUsuario.INTERNO,
    )
    matricula = models.CharField(
        "Matrícula",
        max_length=50,
        blank=True,
    )
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def nome_completo(self):
        return self.get_full_name() or self.username

    @property
    def eh_administrador(self):
        return self.papel in (PapelUsuario.ADMINISTRADOR, PapelUsuario.SUPERUSUARIO)

    @property
    def eh_superusuario_sistema(self):
        return self.papel == PapelUsuario.SUPERUSUARIO