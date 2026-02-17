"""
Services do domínio Empresas.
Lógica de negócio para criação e gestão de empresas.
"""
from django.db import transaction
from .models import Empresa
from nucleo.excecoes import RegraDeNegocioViolada


class EmpresaService:
    """Serviço para operações de negócio relacionadas a empresas."""

    @staticmethod
    @transaction.atomic
    def criar_empresa(
        razao_social: str,
        cnpj: str,
        nome_fantasia: str = "",
        carga_horaria_semanal: float = 44.0,
        tolerancia_minutos: int = 10,
    ) -> Empresa:
        """
        Cria uma nova empresa no sistema.
        
        Args:
            razao_social: Razão social da empresa
            cnpj: CNPJ único da empresa
            nome_fantasia: Nome fantasia (opcional)
            carga_horaria_semanal: Carga horária padrão
            tolerancia_minutos: Tolerância para atrasos
            
        Returns:
            Empresa criada
            
        Raises:
            RegraDeNegocioViolada: Se CNPJ já existe
        """
        # Validar CNPJ único
        if Empresa.objects.filter(cnpj=cnpj).exists():
            raise RegraDeNegocioViolada(
                f"Já existe uma empresa cadastrada com o CNPJ {cnpj}."
            )

        empresa = Empresa.objects.create(
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            cnpj=cnpj,
            carga_horaria_semanal=carga_horaria_semanal,
            tolerancia_minutos=tolerancia_minutos,
            ativa=True,
        )

        return empresa

    @staticmethod
    def desativar_empresa(empresa: Empresa) -> None:
        """
        Desativa uma empresa (soft delete).
        Não permite excluir, apenas marcar como inativa.
        """
        empresa.ativa = False
        empresa.save(update_fields=["ativa", "atualizado_em"])

    @staticmethod
    def reativar_empresa(empresa: Empresa) -> None:
        """Reativa uma empresa previamente desativada."""
        empresa.ativa = True
        empresa.save(update_fields=["ativa", "atualizado_em"])