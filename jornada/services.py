"""Services do domínio Jornada."""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
import base64
from io import BytesIO

from nucleo.excecoes import (
    SequenciaRegistroInvalida,
    ValidacaoLocalizacaoFalhou,
    ValidacaoIPFalhou,
    FotoObrigatoriaAusente,
)
from empresas.models import Empresa
from usuarios.models import Usuario, VinculoUsuario
from .models import (
    RegistroPonto,
    TipoRegistro,
    OrigemRegistro,
    StatusRegistro,
    LocalPermitido,
    IPPermitido,
    SolicitacaoAjuste,
)
from auditoria.services import AuditoriaService
from auditoria.models import TipoAcao


class LocalizacaoService:
    """Service para validação de localização GPS."""
    
    @staticmethod
    def calcular_distancia(
        lat1: Decimal,
        lon1: Decimal,
        lat2: Decimal,
        lon2: Decimal,
    ) -> float:
        """
        Calcula a distância entre duas coordenadas GPS usando a fórmula de Haversine.
        
        Returns:
            Distância em metros
        """
        # Converter para float
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        
        # Converter para radianos
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        
        # Raio da Terra em metros
        r = 6371000
        
        return c * r
    
    @staticmethod
    def validar_localizacao(
        empresa: Empresa,
        latitude: Optional[Decimal],
        longitude: Optional[Decimal],
    ) -> Tuple[bool, Optional[LocalPermitido]]:
        """
        Valida se a localização está dentro de algum local permitido.
        
        Returns:
            (válido, local_utilizado)
        """
        if not latitude or not longitude:
            return False, None
        
        # Buscar todos os locais permitidos ativos da empresa
        locais = LocalPermitido.objects.filter(
            empresa=empresa,
            ativo=True,
        )
        
        for local in locais:
            distancia = LocalizacaoService.calcular_distancia(
                latitude,
                longitude,
                local.latitude,
                local.longitude,
            )
            
            # Se está dentro do raio permitido
            if distancia <= local.raio_metros:
                return True, local
        
        return False, None


class IPService:
    """Service para validação de IP."""
    
    @staticmethod
    def validar_ip(
        empresa: Empresa,
        ip: Optional[str],
    ) -> bool:
        """
        Valida se o IP está na lista de IPs permitidos.
        
        Returns:
            True se o IP é permitido
        """
        if not ip:
            return False
        
        # Verificar se o IP está cadastrado e ativo
        return IPPermitido.objects.filter(
            empresa=empresa,
            ip=ip,
            ativo=True,
        ).exists()


class JornadaService:
    """Service de regras de negócio para registros de ponto."""
    
    @staticmethod
    def obter_proximo_tipo(empresa: Empresa, usuario: Usuario) -> TipoRegistro:
        """Determina o próximo tipo de registro baseado no último registro."""
        ultimo_registro = RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            status=StatusRegistro.ATIVO,
        ).order_by("-data_hora").first()
        
        if not ultimo_registro:
            return TipoRegistro.IN
        
        return TipoRegistro.OUT if ultimo_registro.tipo == TipoRegistro.IN else TipoRegistro.IN
    
    @staticmethod
    def _validar_local_permitido(
        empresa: Empresa,
        latitude: Optional[Decimal],
        longitude: Optional[Decimal],
    ) -> Optional[LocalPermitido]:
        """Valida se está em local permitido. Retorna o local ou None."""
        if not latitude or not longitude:
            return None
        
        valido, local = LocalizacaoService.validar_localizacao(empresa, latitude, longitude)
        return local if valido else None
    
    @staticmethod
    def _validar_ip_permitido(empresa: Empresa, ip_origem: Optional[str]) -> bool:
        """Valida se está em IP permitido."""
        if not ip_origem:
            return False
        return IPService.validar_ip(empresa, ip_origem)
    
    @staticmethod
    def _processar_foto_base64(foto_base64: str, username: str, data_hora: datetime) -> ContentFile:
        """Processa foto em base64 e retorna ContentFile."""
        try:
            from PIL import Image
        except ImportError:
            # Se PIL não estiver disponível, apenas salvar o base64
            pass
        
        # Remover prefixo data:image
        if "," in foto_base64:
            foto_base64 = foto_base64.split(",")[1]
        
        # Decodificar base64
        foto_bytes = base64.b64decode(foto_base64)
        
        try:
            # Tentar otimizar com PIL
            from PIL import Image
            imagem = Image.open(BytesIO(foto_bytes))
            
            # Redimensionar se muito grande (máx 800px)
            if imagem.width > 800 or imagem.height > 800:
                imagem.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Salvar otimizada
            buffer = BytesIO()
            imagem.save(buffer, format="JPEG", quality=85, optimize=True)
            buffer.seek(0)
            foto_bytes = buffer.read()
        except:
            # Se falhar, usar bytes originais
            pass
        
        # Nome do arquivo
        timestamp = data_hora.strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{username}_{timestamp}.jpg"
        
        return ContentFile(foto_bytes, name=nome_arquivo)
    
    @staticmethod
    @transaction.atomic
    def registrar_ponto(
        empresa: Empresa,
        usuario: Usuario,
        origem: str,
        registrado_por: Usuario,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        ip_origem: Optional[str] = None,
        foto_base64: Optional[str] = None,
        observacao: str = "",
        justificativa_sem_foto: str = "",
        data_hora: Optional[datetime] = None,
    ) -> RegistroPonto:
        """
        Registra um ponto de entrada ou saída com todas as validações.
        
        Raises:
            SequenciaRegistroInvalida: Se tentar registrar tipo inválido na sequência
            ValidacaoLocalizacaoFalhou: Se EXTERNO sem GPS
            ValidacaoIPFalhou: Se INTERNO fora dos locais/IPs permitidos
            FotoObrigatoriaAusente: Se primeiro registro do dia sem foto e sem justificativa
        """
        # Data/hora atual se não fornecida
        if data_hora is None:
            data_hora = timezone.now()
        
        # Determinar tipo (IN ou OUT)
        tipo = JornadaService.obter_proximo_tipo(empresa, usuario)
        
        # Validar sequência IN -> OUT -> IN -> OUT
        ultimo_registro = RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            status=StatusRegistro.ATIVO,
        ).order_by("-data_hora").first()
        
        if ultimo_registro:
            if ultimo_registro.tipo == tipo:
                raise SequenciaRegistroInvalida(
                    f"Não é possível registrar {tipo} após {ultimo_registro.tipo}. "
                    f"Sequência esperada: IN → OUT → IN → OUT"
                )
        
        # Verificar se é primeiro registro do dia
        hoje = timezone.localtime(data_hora).date()
        primeiro_registro_dia = not RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            data_hora__date=hoje,
            status=StatusRegistro.ATIVO,
        ).exists()
        
        # VALIDAÇÕES POR VÍNCULO
        validacao_local = False
        local_utilizado = None
        
        if usuario.vinculo == VinculoUsuario.INTERNO:
            # Interno: SEMPRE precisa de GPS E estar em local permitido OU IP permitido
            if not latitude or not longitude:
                raise ValidacaoLocalizacaoFalhou(
                    "Colaboradores INTERNOS devem fornecer localização GPS."
                )
            
            # Verificar se está em local permitido
            local_valido = JornadaService._validar_local_permitido(
                empresa, latitude, longitude
            )
            
            # Verificar se está em IP permitido
            ip_valido = JornadaService._validar_ip_permitido(empresa, ip_origem)
            
            if not local_valido and not ip_valido:
                raise ValidacaoLocalizacaoFalhou(
                    "Você não está em um local ou rede permitidos. "
                    "Conecte-se à rede da empresa ou vá até um local cadastrado."
                )
            
            validacao_local = local_valido is not None
            local_utilizado = local_valido
        
        elif usuario.vinculo == VinculoUsuario.EXTERNO:
            # Externo: SEMPRE precisa de GPS (não precisa estar em local específico)
            if not latitude or not longitude:
                raise ValidacaoLocalizacaoFalhou(
                    "Colaboradores EXTERNOS devem fornecer localização GPS."
                )
            
            validacao_local = False
            local_utilizado = None
        
        else:  # CONFIANCA
            # Confiança: Não precisa de GPS nem local
            validacao_local = False
            local_utilizado = None
        
        # VALIDAÇÃO DE FOTO (apenas primeiro registro do dia)
        foto_processada = None
        if primeiro_registro_dia:
            if foto_base64:
                # Processar foto base64
                foto_processada = JornadaService._processar_foto_base64(
                    foto_base64, usuario.username, data_hora
                )
            elif not justificativa_sem_foto:
                # Se não tem foto E não tem justificativa, exigir
                raise FotoObrigatoriaAusente(
                    "Foto obrigatória para o primeiro registro do dia. "
                    "Caso não consiga tirar foto, informe o motivo."
                )
        
        # Criar registro
        registro = RegistroPonto.objects.create(
            empresa=empresa,
            usuario=usuario,
            tipo=tipo,
            data_hora=data_hora,
            origem=origem,
            registrado_por=registrado_por,
            latitude=latitude,
            longitude=longitude,
            ip_origem=ip_origem,
            foto=foto_processada,
            validacao_local=validacao_local,
            local_utilizado=local_utilizado,
            observacao=observacao,
            justificativa_sem_foto=justificativa_sem_foto,
        )
        
        # Registrar auditoria
        descricao_auditoria = f"Registro de ponto {tipo} para {usuario.username}"
        if justificativa_sem_foto:
            descricao_auditoria += f" (SEM FOTO: {justificativa_sem_foto[:50]})"
        
        AuditoriaService.registrar_acao(
            empresa=empresa,
            usuario=registrado_por,
            tipo_acao=TipoAcao.REGISTRO_PONTO,
            descricao=descricao_auditoria,
            objeto=registro,
            ip_origem=ip_origem,
        )
        
        return registro


class SolicitacaoAjusteService:
    """Service para gerenciar solicitações de ajuste de ponto."""
    
    @staticmethod
    @transaction.atomic
    def criar_solicitacao(
        solicitante: Usuario,
        empresa: Empresa,
        registro_original: RegistroPonto,
        data_hora_desejada: datetime,
        justificativa: str,
    ) -> SolicitacaoAjuste:
        """Cria uma nova solicitação de ajuste."""
        solicitacao = SolicitacaoAjuste.objects.create(
            empresa=empresa,
            solicitante=solicitante,
            registro_original=registro_original,
            data_hora_desejada=data_hora_desejada,
            justificativa=justificativa,
            status=SolicitacaoAjuste.StatusSolicitacao.PENDENTE,
        )
        
        # Registrar auditoria
        AuditoriaService.registrar_acao(
            empresa=empresa,
            usuario=solicitante,
            tipo_acao=TipoAcao.SOLICITACAO_AJUSTE,
            descricao=f"Solicitação de ajuste criada por {solicitante.username}",
            objeto=solicitacao,
        )
        
        return solicitacao
    
    @staticmethod
    @transaction.atomic
    def aprovar_solicitacao(
        solicitacao: SolicitacaoAjuste,
        analisado_por: Usuario,
        observacao_analise: str = "",
        ip_origem: Optional[str] = None,
    ) -> RegistroPonto:
        """
        Aprova uma solicitação de ajuste.
        
        - Marca o registro original como SUBSTITUIDO
        - Cria um novo registro com a data/hora corrigida
        - Marca a solicitação como APROVADO
        """
        # Marcar registro original como substituído
        registro_original = solicitacao.registro_original
        registro_original.status = StatusRegistro.SUBSTITUIDO
        registro_original.save()
        
        # Criar novo registro ajustado
        registro_ajustado = RegistroPonto.objects.create(
            empresa=solicitacao.empresa,
            usuario=solicitacao.solicitante,
            tipo=registro_original.tipo,
            data_hora=solicitacao.data_hora_desejada,
            origem=OrigemRegistro.AJUSTE,
            status=StatusRegistro.ATIVO,
            substitui=registro_original,
            observacao=f"Ajuste aprovado por {analisado_por.username}. {solicitacao.justificativa}",
            registrado_por=analisado_por,
            latitude=registro_original.latitude,
            longitude=registro_original.longitude,
            ip_origem=registro_original.ip_origem,
            validacao_local=registro_original.validacao_local,
            local_utilizado=registro_original.local_utilizado,
            foto=registro_original.foto,
        )
        
        # Atualizar solicitação
        solicitacao.status = SolicitacaoAjuste.StatusSolicitacao.APROVADO
        solicitacao.analisado_por = analisado_por
        solicitacao.data_analise = timezone.now()
        solicitacao.observacao_analise = observacao_analise
        solicitacao.save()
        
        # Registrar auditoria
        AuditoriaService.registrar_acao(
            empresa=solicitacao.empresa,
            usuario=analisado_por,
            tipo_acao=TipoAcao.APROVACAO_AJUSTE,
            descricao=f"Ajuste aprovado por {analisado_por.username} para {solicitacao.solicitante.username}",
            objeto=solicitacao,
            ip_origem=ip_origem,
        )
        
        return registro_ajustado
    
    @staticmethod
    @transaction.atomic
    def rejeitar_solicitacao(
        solicitacao: SolicitacaoAjuste,
        analisado_por: Usuario,
        observacao_analise: str,
        ip_origem: Optional[str] = None,
    ) -> SolicitacaoAjuste:
        """Rejeita uma solicitação de ajuste."""
        solicitacao.status = SolicitacaoAjuste.StatusSolicitacao.REJEITADO
        solicitacao.analisado_por = analisado_por
        solicitacao.data_analise = timezone.now()
        solicitacao.observacao_analise = observacao_analise
        solicitacao.save()
        
        # Registrar auditoria
        AuditoriaService.registrar_acao(
            empresa=solicitacao.empresa,
            usuario=analisado_por,
            tipo_acao=TipoAcao.REJEICAO_AJUSTE,
            descricao=f"Ajuste rejeitado por {analisado_por.username} para {solicitacao.solicitante.username}",
            objeto=solicitacao,
            ip_origem=ip_origem,
        )
        
        return solicitacao