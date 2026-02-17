"""
Exceções de domínio do OnTime.
Usar exceções semânticas em vez de strings ou códigos genéricos.
"""


class OnTimeExcecao(Exception):
    """Exceção base do sistema OnTime."""
    pass


class RegraDeNegocioViolada(OnTimeExcecao):
    """
    Lançada quando uma regra de negócio é violada.
    Deve ser capturada nas views e retornada como erro de formulário.
    """
    pass


class SequenciaRegistroInvalida(RegraDeNegocioViolada):
    """
    Lançada quando a sequência IN→OUT é violada.
    Ex: tentar registrar OUT sem IN aberto.
    """
    pass


class EmpresaNaoIdentificada(OnTimeExcecao):
    """Lançada quando o contexto de empresa não está disponível."""
    pass


class PermissaoNegada(OnTimeExcecao):
    """Lançada quando o usuário não tem permissão para a ação."""
    pass


class FechamentoJaRealizado(RegraDeNegocioViolada):
    """Lançada ao tentar modificar registros de uma semana já fechada."""
    pass

class ValidacaoLocalizacaoFalhou(Exception):
    """Exceção lançada quando validação de GPS falha."""
    pass


class ValidacaoIPFalhou(Exception):
    """Exceção lançada quando validação de IP falha."""
    pass


class FotoObrigatoriaAusente(Exception):
    """Exceção lançada quando foto obrigatória não foi fornecida."""
    pass