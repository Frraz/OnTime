"""Context processors globais do OnTime."""


def empresa_ativa(request):
    """Injeta a empresa ativa no contexto de todos os templates."""
    return {
        "empresa_ativa": getattr(request, "empresa", None),
    }