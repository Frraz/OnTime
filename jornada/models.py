"""Models do domínio Jornada."""
from decimal import Decimal
from django.db import models
from django.utils import timezone

from nucleo.models import ModeloBase
from empresas.models import Empresa
from usuarios.models import Usuario


class TipoRegistro(models.TextChoices):
    """Tipo de registro de ponto."""
    IN = "IN", "Entrada"
    OUT = "OUT", "Saída"


class OrigemRegistro(models.TextChoices):
    """Origem do registro de ponto."""
    SISTEMA = "SISTEMA", "Sistema Web"
    MOBILE = "MOBILE", "Aplicativo Mobile"
    AJUSTE = "AJUSTE", "Ajuste Manual"


class StatusRegistro(models.TextChoices):
    """Status do registro de ponto."""
    ATIVO = "ATIVO", "Ativo"
    SUBSTITUIDO = "SUBSTITUIDO", "Substituído por Ajuste"
    CANCELADO = "CANCELADO", "Cancelado"


class RegistroPonto(ModeloBase):
    """Registro de ponto de entrada/saída."""
    
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="registros_ponto",
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="registros_ponto",
    )
    tipo = models.CharField(max_length=3, choices=TipoRegistro.choices)
    data_hora = models.DateTimeField()
    origem = models.CharField(max_length=10, choices=OrigemRegistro.choices)
    status = models.CharField(
        max_length=12,
        choices=StatusRegistro.choices,
        default=StatusRegistro.ATIVO,
    )
    
    # Registro que este substitui (quando é ajuste)
    substitui = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="substituido_por",
    )
    
    # Observações
    observacao = models.TextField(blank=True, default="")
    justificativa_sem_foto = models.TextField(
        blank=True, 
        default="",
        verbose_name="Justificativa para registro sem foto",
        help_text="Motivo informado pelo colaborador ao registrar sem foto"
    )
    
    # Quem registrou (pode ser diferente do usuário em registros manuais)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="registros_criados",
    )
    
    # Validações
    foto = models.ImageField(
        upload_to="fotos_ponto/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    validacao_local = models.BooleanField(default=False)
    local_utilizado = models.ForeignKey(
        "LocalPermitido",  # ← MUDANÇA AQUI: usar string ao invés da classe
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_ponto",
    )
    
    class Meta:
        db_table = "jornada_registroponto"
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["empresa", "usuario", "data_hora"]),
            models.Index(fields=["empresa", "status"]),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} - {self.data_hora}"
    

class LocalPermitido(ModeloBase):
    """Locais permitidos para registro de ponto (GPS)."""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="locais_permitidos",
    )
    nome = models.CharField(
        "Nome do Local",
        max_length=100,
        help_text="Ex: Matriz, Filial SP, Escritório RJ",
    )
    latitude = models.DecimalField(
        "Latitude",
        max_digits=10,
        decimal_places=7,
        help_text="Coordenada de latitude do centro do local",
    )
    longitude = models.DecimalField(
        "Longitude",
        max_digits=10,
        decimal_places=7,
        help_text="Coordenada de longitude do centro do local",
    )
    raio_metros = models.PositiveIntegerField(
        "Raio em Metros",
        default=100,
        help_text="Raio de tolerância em metros a partir do ponto central",
    )
    ativo = models.BooleanField(
        "Ativo",
        default=True,
    )
    
    class Meta:
        db_table = "jornada_localpermitido"
        verbose_name = "Local Permitido"
        verbose_name_plural = "Locais Permitidos"
        ordering = ["nome"]
        unique_together = [["empresa", "nome"]]
    
    def __str__(self):
        return f"{self.nome} ({self.raio_metros}m)"


class IPPermitido(ModeloBase):
    """IPs permitidos para registro de ponto."""
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        related_name="ips_permitidos",
    )
    nome = models.CharField(
        "Nome",
        max_length=100,
        help_text="Ex: Rede Matriz, WiFi Filial SP",
    )
    ip = models.GenericIPAddressField(
        "Endereço IP",
        help_text="IP fixo da rede local",
    )
    ativo = models.BooleanField(
        "Ativo",
        default=True,
    )
    
    class Meta:
        db_table = "jornada_ippermitido"
        verbose_name = "IP Permitido"
        verbose_name_plural = "IPs Permitidos"
        ordering = ["nome"]
        unique_together = [["empresa", "ip"]]
    
    def __str__(self):
        return f"{self.nome} ({self.ip})"


class SolicitacaoAjuste(ModeloBase):
    """Solicitação de ajuste de ponto por colaborador."""
    
    class StatusSolicitacao(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        APROVADO = "APROVADO", "Aprovado"
        REJEITADO = "REJEITADO", "Rejeitado"
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="Empresa",
    )
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        verbose_name="Solicitante",
        related_name="solicitacoes_ajuste",
    )
    registro_original = models.ForeignKey(
        RegistroPonto,
        on_delete=models.PROTECT,
        verbose_name="Registro Original",
        related_name="solicitacoes_ajuste",
    )
    data_hora_desejada = models.DateTimeField(
        "Data/Hora Desejada",
        help_text="Data e hora correta que deveria ter sido registrada",
    )
    justificativa = models.TextField(
        "Justificativa",
        help_text="Motivo da solicitação de ajuste",
    )
    status = models.CharField(
        "Status",
        max_length=10,
        choices=StatusSolicitacao.choices,
        default=StatusSolicitacao.PENDENTE,
    )
    analisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Analisado Por",
        related_name="analises_ajuste",
    )
    data_analise = models.DateTimeField(
        "Data da Análise",
        null=True,
        blank=True,
    )
    observacao_analise = models.TextField(
        "Observação da Análise",
        blank=True,
        default="",
    )
    
    class Meta:
        db_table = "jornada_solicitacaoajuste"
        verbose_name = "Solicitação de Ajuste"
        verbose_name_plural = "Solicitações de Ajuste"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "status"]),
            models.Index(fields=["solicitante", "status"]),
        ]
    
    def __str__(self):
        return f"{self.solicitante.username} - {self.get_status_display()}"