"""Models do domínio Auditoria."""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from nucleo.models import ModeloBase
from empresas.models import Empresa
from usuarios.models import Usuario


class TipoAcao(models.TextChoices):
    """Tipos de ações auditadas."""
    CRIACAO = "CRIACAO", "Criação"
    EDICAO = "EDICAO", "Edição"
    EXCLUSAO = "EXCLUSAO", "Exclusão"
    REGISTRO_PONTO = "REGISTRO_PONTO", "Registro de Ponto"
    AJUSTE_PONTO = "AJUSTE_PONTO", "Ajuste de Ponto"
    FECHAMENTO_SEMANA = "FECHAMENTO_SEMANA", "Fechamento Semanal"
    REABERTURA_SEMANA = "REABERTURA_SEMANA", "Reabertura Semanal"
    APROVACAO_AJUSTE = "APROVACAO_AJUSTE", "Aprovação de Ajuste"
    REJEICAO_AJUSTE = "REJEICAO_AJUSTE", "Rejeição de Ajuste"


class LogAuditoria(ModeloBase):
    """Log de auditoria de todas as ações críticas do sistema."""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        null=True,
        blank=True,
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Usuário",
        help_text="Usuário que realizou a ação",
    )
    tipo_acao = models.CharField(
        "Tipo de Ação",
        max_length=20,
        choices=TipoAcao.choices,
    )
    descricao = models.TextField(
        "Descrição",
        help_text="Descrição detalhada da ação realizada",
    )
    
    # Generic Foreign Key para referenciar qualquer objeto
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    objeto_relacionado = GenericForeignKey("content_type", "object_id")
    
    # Dados adicionais
    ip_origem = models.GenericIPAddressField(
        "IP de Origem",
        null=True,
        blank=True,
    )
    dados_antes = models.JSONField(
        "Dados Antes",
        null=True,
        blank=True,
        help_text="Estado do objeto antes da alteração (JSON)",
    )
    dados_depois = models.JSONField(
        "Dados Depois",
        null=True,
        blank=True,
        help_text="Estado do objeto depois da alteração (JSON)",
    )
    
    class Meta:
        db_table = "auditoria_logauditoria"
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "criado_em"]),
            models.Index(fields=["usuario", "criado_em"]),
            models.Index(fields=["tipo_acao"]),
            models.Index(fields=["content_type", "object_id"]),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Sistema"
        return f"{usuario_str} - {self.get_tipo_acao_display()} - {self.criado_em.strftime('%d/%m/%Y %H:%M')}"