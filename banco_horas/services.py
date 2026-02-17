"""
Services do domínio Banco de Horas.
Lógica de cálculo e gestão de saldos.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import SaldoBancoHoras
from jornada.models import RegistroPonto, TipoRegistro, StatusRegistro
from usuarios.models import Usuario
from empresas.models import Empresa
from nucleo.calculos import calcular_duracao, timedelta_para_decimal, somar_timedeltas
from nucleo.excecoes import RegraDeNegocioViolada


class BancoHorasService:
    """Serviço para cálculo e gestão de banco de horas."""

    @staticmethod
    def calcular_horas_trabalhadas_dia(
        usuario: Usuario,
        empresa: Empresa,
        dia: date,
    ) -> Decimal:
        """
        Calcula as horas trabalhadas em um dia específico.
        
        Soma todos os pares IN→OUT do dia.
        """
        registros = RegistroPonto.objects.filter(
            empresa=empresa,
            usuario=usuario,
            data_hora__date=dia,
            status=StatusRegistro.ATIVO,
        ).order_by("data_hora")

        total_horas = timedelta(0)
        entrada = None

        for registro in registros:
            if registro.tipo == TipoRegistro.ENTRADA:
                entrada = registro.data_hora
            elif registro.tipo == TipoRegistro.SAIDA and entrada:
                duracao = calcular_duracao(entrada, registro.data_hora)
                total_horas += duracao
                entrada = None

        return timedelta_para_decimal(total_horas)

    @staticmethod
    def calcular_horas_trabalhadas_semana(
        usuario: Usuario,
        empresa: Empresa,
        ano: int,
        semana: int,
    ) -> Decimal:
        """
        Calcula as horas trabalhadas em uma semana específica.
        """
        # Determinar o range de datas da semana
        primeiro_dia = datetime.strptime(f"{ano}-W{semana:02d}-1", "%Y-W%W-%w").date()
        ultimo_dia = primeiro_dia + timedelta(days=6)

        total_horas = Decimal("0.00")

        # Calcular para cada dia da semana
        dia_atual = primeiro_dia
        while dia_atual <= ultimo_dia:
            horas_dia = BancoHorasService.calcular_horas_trabalhadas_dia(
                usuario, empresa, dia_atual
            )
            total_horas += horas_dia
            dia_atual += timedelta(days=1)

        return total_horas

    @staticmethod
    def obter_saldo_anterior(
        usuario: Usuario,
        empresa: Empresa,
        ano: int,
        semana: int,
    ) -> Decimal:
        """
        Obtém o saldo acumulado da semana anterior.
        """
        # Calcular semana anterior
        if semana == 1:
            ano_anterior = ano - 1
            semana_anterior = 52  # Assumindo ano com 52 semanas
        else:
            ano_anterior = ano
            semana_anterior = semana - 1

        saldo_anterior_obj = SaldoBancoHoras.objects.filter(
            empresa=empresa,
            usuario=usuario,
            ano=ano_anterior,
            semana=semana_anterior,
        ).first()

        if saldo_anterior_obj:
            return saldo_anterior_obj.saldo_acumulado

        return Decimal("0.00")

    @staticmethod
    @transaction.atomic
    def calcular_saldo_semana(
        usuario: Usuario,
        empresa: Empresa,
        ano: int,
        semana: int,
        fechar: bool = False,
        fechado_por: Usuario = None,
    ) -> SaldoBancoHoras:
        """
        Calcula ou atualiza o saldo de banco de horas de uma semana.
        
        Args:
            usuario: Usuário
            empresa: Empresa
            ano: Ano
            semana: Número da semana
            fechar: Se True, marca a semana como fechada
            fechado_por: Quem está fechando
            
        Returns:
            SaldoBancoHoras criado ou atualizado
        """
        # Calcular horas trabalhadas
        horas_trabalhadas = BancoHorasService.calcular_horas_trabalhadas_semana(
            usuario, empresa, ano, semana
        )

        # Horas esperadas = carga horária da empresa
        horas_esperadas = empresa.carga_horaria_semanal

        # Saldo da semana
        saldo_semana = horas_trabalhadas - horas_esperadas

        # Saldo acumulado = saldo anterior + saldo desta semana
        saldo_anterior = BancoHorasService.obter_saldo_anterior(
            usuario, empresa, ano, semana
        )
        saldo_acumulado = saldo_anterior + saldo_semana

        # Criar ou atualizar
        saldo, created = SaldoBancoHoras.objects.update_or_create(
            empresa=empresa,
            usuario=usuario,
            ano=ano,
            semana=semana,
            defaults={
                "horas_trabalhadas": horas_trabalhadas,
                "horas_esperadas": horas_esperadas,
                "saldo_semana": saldo_semana,
                "saldo_acumulado": saldo_acumulado,
            },
        )

        # Fechar se solicitado
        if fechar and not saldo.fechado:
            saldo.fechado = True
            saldo.data_fechamento = timezone.now()
            saldo.fechado_por = fechado_por
            saldo.save(update_fields=["fechado", "data_fechamento", "fechado_por"])

        return saldo

    @staticmethod
    def obter_saldo_atual(usuario: Usuario, empresa: Empresa) -> Decimal:
        """
        Retorna o saldo acumulado mais recente do usuário.
        """
        ultimo_saldo = SaldoBancoHoras.objects.filter(
            empresa=empresa,
            usuario=usuario,
        ).order_by("-ano", "-semana").first()

        if ultimo_saldo:
            return ultimo_saldo.saldo_acumulado

        return Decimal("0.00")