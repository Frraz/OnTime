"""Services do domínio Auditoria."""
from typing import Optional, Any, Dict
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import LogAuditoria, TipoAcao
from empresas.models import Empresa
from usuarios.models import Usuario


class AuditoriaService:
    """Service para registrar logs de auditoria."""
    
    @staticmethod
    def registrar(
        tipo_acao: TipoAcao,
        descricao: str,
        usuario: Optional[Usuario] = None,
        empresa: Optional[Empresa] = None,
        objeto_relacionado: Optional[models.Model] = None,
        ip_origem: Optional[str] = None,
        dados_antes: Optional[Dict[str, Any]] = None,
        dados_depois: Optional[Dict[str, Any]] = None,
    ) -> LogAuditoria:
        """
        Registra uma ação no log de auditoria.
        
        Args:
            tipo_acao: Tipo da ação realizada
            descricao: Descrição detalhada da ação
            usuario: Usuário que realizou a ação
            empresa: Empresa relacionada
            objeto_relacionado: Objeto que foi afetado pela ação
            ip_origem: IP de onde a ação foi realizada
            dados_antes: Estado do objeto antes da ação
            dados_depois: Estado do objeto depois da ação
        
        Returns:
            LogAuditoria criado
        """
        log = LogAuditoria(
            tipo_acao=tipo_acao,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            ip_origem=ip_origem,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
        )
        
        # Se houver objeto relacionado, configurar GenericForeignKey
        if objeto_relacionado:
            log.content_type = ContentType.objects.get_for_model(objeto_relacionado)
            log.object_id = objeto_relacionado.pk
        
        log.save()
        return log
    
    @staticmethod
    def registrar_criacao(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        objeto: models.Model,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar criação de objeto."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.CRIACAO,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=objeto,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_edicao(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        objeto: models.Model,
        dados_antes: Dict[str, Any],
        dados_depois: Dict[str, Any],
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar edição de objeto."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.EDICAO,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=objeto,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_exclusao(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        objeto: models.Model,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar exclusão de objeto."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.EXCLUSAO,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=objeto,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_registro_ponto(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        registro_ponto,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar ponto."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.REGISTRO_PONTO,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=registro_ponto,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_ajuste_ponto(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        registro_ponto,
        dados_antes: Dict[str, Any],
        dados_depois: Dict[str, Any],
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar ajuste de ponto."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.AJUSTE_PONTO,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=registro_ponto,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_fechamento_semana(
        descricao: str,
        usuario: Optional[Usuario],
        empresa: Empresa,
        saldo_banco_horas,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar fechamento semanal."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.FECHAMENTO_SEMANA,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=saldo_banco_horas,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_reabertura_semana(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        saldo_banco_horas,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar reabertura semanal."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.REABERTURA_SEMANA,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=saldo_banco_horas,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_aprovacao_ajuste(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        solicitacao_ajuste,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar aprovação de ajuste."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.APROVACAO_AJUSTE,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=solicitacao_ajuste,
            ip_origem=ip_origem,
        )
    
    @staticmethod
    def registrar_rejeicao_ajuste(
        descricao: str,
        usuario: Usuario,
        empresa: Empresa,
        solicitacao_ajuste,
        ip_origem: Optional[str] = None,
    ) -> LogAuditoria:
        """Atalho para registrar rejeição de ajuste."""
        return AuditoriaService.registrar(
            tipo_acao=TipoAcao.REJEICAO_AJUSTE,
            descricao=descricao,
            usuario=usuario,
            empresa=empresa,
            objeto_relacionado=solicitacao_ajuste,
            ip_origem=ip_origem,
        )