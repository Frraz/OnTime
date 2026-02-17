"""Services de estatísticas e dashboard."""
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Tuple
from collections import defaultdict

from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from empresas.models import Empresa
from usuarios.models import Usuario
from .models import RegistroPonto, StatusRegistro, TipoRegistro
from banco_horas.models import SaldoBancoHoras


class DashboardService:
    """Service para gerar dados do dashboard."""
    
    @staticmethod
    def get_resumo_hoje(usuario: Usuario, empresa: Empresa) -> Dict:
        """
        Resumo do dia atual.
        
        Returns:
            {
                'registros_hoje': int,
                'primeira_entrada': datetime,
                'ultima_saida': datetime,
                'horas_hoje': Decimal,
                'dentro': bool,
            }
        """
        hoje = timezone.localtime().date()
        
        registros = RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            data_hora__date=hoje,
            status=StatusRegistro.ATIVO,
        ).order_by('data_hora')
        
        primeira_entrada = None
        ultima_saida = None
        horas_hoje = Decimal('0')
        dentro = False
        
        if registros.exists():
            # Primeira entrada
            primeira_in = registros.filter(tipo=TipoRegistro.IN).first()
            if primeira_in:
                primeira_entrada = primeira_in.data_hora
            
            # Última saída
            ultima_out = registros.filter(tipo=TipoRegistro.OUT).last()
            if ultima_out:
                ultima_saida = ultima_out.data_hora
            
            # Calcular horas trabalhadas hoje
            entrada_temp = None
            for registro in registros:
                if registro.tipo == TipoRegistro.IN:
                    entrada_temp = registro.data_hora
                    dentro = True
                elif registro.tipo == TipoRegistro.OUT and entrada_temp:
                    duracao = (registro.data_hora - entrada_temp).total_seconds() / 3600
                    horas_hoje += Decimal(str(duracao))
                    entrada_temp = None
                    dentro = False
        
        return {
            'registros_hoje': registros.count(),
            'primeira_entrada': primeira_entrada,
            'ultima_saida': ultima_saida,
            'horas_hoje': round(horas_hoje, 2),
            'dentro': dentro,
        }
    
    @staticmethod
    def get_semana_atual(usuario: Usuario, empresa: Empresa) -> Dict:
        """
        Resumo da semana atual.
        
        Returns:
            {
                'ano': int,
                'semana': int,
                'horas_trabalhadas': Decimal,
                'horas_esperadas': Decimal,
                'saldo': Decimal,
                'progresso': int (0-100),
            }
        """
        hoje = date.today()
        ano = hoje.isocalendar()[0]
        semana = hoje.isocalendar()[1]
        
        saldo = SaldoBancoHoras.objects.filter(
            empresa=empresa,
            usuario=usuario,
            ano=ano,
            semana=semana,
        ).first()
        
        if saldo:
            progresso = 0
            if saldo.horas_esperadas > 0:
                progresso = int((float(saldo.horas_trabalhadas) / float(saldo.horas_esperadas)) * 100)
            
            return {
                'ano': ano,
                'semana': semana,
                'horas_trabalhadas': saldo.horas_trabalhadas,
                'horas_esperadas': saldo.horas_esperadas,
                'saldo': saldo.saldo_semana,
                'progresso': min(progresso, 100),  # Máximo 100%
            }
        
        return {
            'ano': ano,
            'semana': semana,
            'horas_trabalhadas': Decimal('0'),
            'horas_esperadas': empresa.carga_horaria_semanal,
            'saldo': Decimal('0'),
            'progresso': 0,
        }
    
    @staticmethod
    def get_ultimas_semanas(
        usuario: Usuario,
        empresa: Empresa,
        quantidade: int = 12
    ) -> List[Dict]:
        """
        Dados das últimas N semanas para gráfico.
        
        Returns:
            [
                {
                    'label': '2026S07',
                    'trabalhadas': 44.0,
                    'esperadas': 44.0,
                    'saldo': 0.0,
                },
                ...
            ]
        """
        saldos = SaldoBancoHoras.objects.filter(
            empresa=empresa,
            usuario=usuario,
        ).order_by('-ano', '-semana')[:quantidade]
        
        dados = []
        for saldo in reversed(saldos):
            dados.append({
                'label': f"{saldo.ano}S{saldo.semana:02d}",
                'trabalhadas': float(saldo.horas_trabalhadas),
                'esperadas': float(saldo.horas_esperadas),
                'saldo': float(saldo.saldo_semana),
            })
        
        return dados
    
    @staticmethod
    def get_evolucao_banco_horas(
        usuario: Usuario,
        empresa: Empresa,
        quantidade: int = 12
    ) -> List[Dict]:
        """
        Evolução do saldo acumulado para gráfico.
        
        Returns:
            [
                {
                    'label': '2026S07',
                    'saldo_acumulado': -5.5,
                },
                ...
            ]
        """
        saldos = SaldoBancoHoras.objects.filter(
            empresa=empresa,
            usuario=usuario,
        ).order_by('-ano', '-semana')[:quantidade]
        
        dados = []
        for saldo in reversed(saldos):
            dados.append({
                'label': f"{saldo.ano}S{saldo.semana:02d}",
                'saldo_acumulado': float(saldo.saldo_acumulado),
            })
        
        return dados
    
    @staticmethod
    def get_horas_por_dia_semana(
        usuario: Usuario,
        empresa: Empresa,
    ) -> List[Dict]:
        """
        Média de horas trabalhadas por dia da semana (últimas 4 semanas).
        
        Returns:
            [
                {'dia': 'Segunda', 'horas': 8.5},
                {'dia': 'Terça', 'horas': 8.2},
                ...
            ]
        """
        # Últimas 4 semanas
        hoje = timezone.localtime().date()
        data_inicio = hoje - timedelta(days=28)
        
        registros = RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            data_hora__date__gte=data_inicio,
            status=StatusRegistro.ATIVO,
        ).order_by('data_hora')
        
        # Agrupar por dia da semana
        horas_por_dia = defaultdict(list)
        
        # Calcular horas por data
        horas_por_data = defaultdict(Decimal)
        entrada_temp = None
        
        for registro in registros:
            data = registro.data_hora.date()
            
            if registro.tipo == TipoRegistro.IN:
                entrada_temp = registro.data_hora
            elif registro.tipo == TipoRegistro.OUT and entrada_temp:
                if entrada_temp.date() == data:  # Mesmo dia
                    duracao = (registro.data_hora - entrada_temp).total_seconds() / 3600
                    horas_por_data[data] += Decimal(str(duracao))
                entrada_temp = None
        
        # Agrupar por dia da semana
        for data, horas in horas_por_data.items():
            dia_semana = data.weekday()  # 0=segunda, 6=domingo
            horas_por_dia[dia_semana].append(float(horas))
        
        # Calcular média
        dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        resultado = []
        
        for i, dia in enumerate(dias_semana):
            if horas_por_dia[i]:
                media = sum(horas_por_dia[i]) / len(horas_por_dia[i])
            else:
                media = 0
            
            resultado.append({
                'dia': dia,
                'horas': round(media, 2),
            })
        
        return resultado
    
    @staticmethod
    def get_ranking_usuarios(empresa: Empresa, quantidade: int = 10) -> List[Dict]:
        """
        Ranking de usuários por horas trabalhadas no mês atual.
        
        Returns:
            [
                {
                    'usuario': 'joao',
                    'nome': 'João Silva',
                    'horas': 180.5,
                    'saldo': 5.5,
                },
                ...
            ]
        """
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Buscar todos os usuários ativos
        usuarios = Usuario.objects.filter(
            empresa=empresa,
            ativo=True,
        )
        
        ranking = []
        
        for usuario in usuarios:
            # Calcular horas do mês
            registros = RegistroPonto.objects.filter(
                empresa=empresa,
                usuario=usuario,
                data_hora__date__gte=inicio_mes,
                status=StatusRegistro.ATIVO,
            ).order_by('data_hora')
            
            horas_mes = Decimal('0')
            entrada_temp = None
            
            for registro in registros:
                if registro.tipo == TipoRegistro.IN:
                    entrada_temp = registro.data_hora
                elif registro.tipo == TipoRegistro.OUT and entrada_temp:
                    duracao = (registro.data_hora - entrada_temp).total_seconds() / 3600
                    horas_mes += Decimal(str(duracao))
                    entrada_temp = None
            
            # Saldo acumulado atual
            saldo_atual = SaldoBancoHoras.objects.filter(
                empresa=empresa,
                usuario=usuario,
            ).order_by('-ano', '-semana').first()
            
            ranking.append({
                'usuario': usuario.username,
                'nome': usuario.nome_completo or usuario.username,
                'horas': float(horas_mes),
                'saldo': float(saldo_atual.saldo_acumulado) if saldo_atual else 0.0,
            })
        
        # Ordenar por horas trabalhadas
        ranking.sort(key=lambda x: x['horas'], reverse=True)
        
        return ranking[:quantidade]
    
    @staticmethod
    def get_estatisticas_gerais(empresa: Empresa) -> Dict:
        """
        Estatísticas gerais da empresa.
        
        Returns:
            {
                'total_usuarios': int,
                'usuarios_ativos_hoje': int,
                'media_horas_dia': Decimal,
                'total_registros_mes': int,
            }
        """
        hoje = timezone.localtime().date()
        inicio_mes = hoje.replace(day=1)
        
        # Total de usuários
        total_usuarios = Usuario.objects.filter(
            empresa=empresa,
            ativo=True,
        ).count()
        
        # Usuários que bateram ponto hoje
        usuarios_ativos_hoje = RegistroPonto.objects.filter(
            empresa=empresa,
            data_hora__date=hoje,
            status=StatusRegistro.ATIVO,
        ).values('usuario').distinct().count()
        
        # Total de registros no mês
        total_registros_mes = RegistroPonto.objects.filter(
            empresa=empresa,
            data_hora__date__gte=inicio_mes,
            status=StatusRegistro.ATIVO,
        ).count()
        
        # Média de horas por dia (últimos 30 dias)
        data_inicio = hoje - timedelta(days=30)
        
        registros = RegistroPonto.objects.filter(
            empresa=empresa,
            data_hora__date__gte=data_inicio,
            status=StatusRegistro.ATIVO,
        ).order_by('data_hora')
        
        horas_por_data = defaultdict(Decimal)
        entrada_temp = {}
        
        for registro in registros:
            usuario_id = registro.usuario_id
            data = registro.data_hora.date()
            
            if registro.tipo == TipoRegistro.IN:
                entrada_temp[usuario_id] = registro.data_hora
            elif registro.tipo == TipoRegistro.OUT and usuario_id in entrada_temp:
                if entrada_temp[usuario_id].date() == data:
                    duracao = (registro.data_hora - entrada_temp[usuario_id]).total_seconds() / 3600
                    horas_por_data[data] += Decimal(str(duracao))
                del entrada_temp[usuario_id]
        
        media_horas = Decimal('0')
        if horas_por_data:
            total_horas = sum(horas_por_data.values())
            media_horas = total_horas / len(horas_por_data)
        
        return {
            'total_usuarios': total_usuarios,
            'usuarios_ativos_hoje': usuarios_ativos_hoje,
            'media_horas_dia': round(media_horas, 2),
            'total_registros_mes': total_registros_mes,
        }