"""
Funções puras de cálculo de jornada.
Sem dependências de models — apenas lógica matemática.
Facilita testes unitários isolados.
"""
from datetime import timedelta, datetime
from decimal import Decimal


def calcular_duracao(entrada: datetime, saida: datetime) -> timedelta:
    """Retorna a duração entre entrada e saída."""
    if saida <= entrada:
        raise ValueError("Saída deve ser posterior à entrada.")
    return saida - entrada


def timedelta_para_decimal(duracao: timedelta) -> Decimal:
    """Converte timedelta em horas decimais. Ex: 1h30min → 1.5"""
    total_segundos = duracao.total_seconds()
    horas = Decimal(str(total_segundos / 3600)).quantize(Decimal("0.01"))
    return horas


def calcular_saldo(
    horas_trabalhadas: Decimal,
    carga_horaria: Decimal,
) -> Decimal:
    """
    Calcula o saldo de banco de horas.
    Positivo = horas extras. Negativo = débito.
    """
    return horas_trabalhadas - carga_horaria


def somar_timedeltas(durações: list[timedelta]) -> timedelta:
    """Soma uma lista de timedeltas. Retorna zero se lista vazia."""
    return sum(durações, timedelta(0))