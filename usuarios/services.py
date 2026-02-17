"""
Services do domínio Usuários.
Lógica de negócio para criação e gestão de usuários.
"""
from django.db import transaction
from django.contrib.auth.hashers import make_password
from .models import Usuario, PapelUsuario, VinculoUsuario
from empresas.models import Empresa
from nucleo.excecoes import RegraDeNegocioViolada


class UsuarioService:
    """Serviço para operações de negócio relacionadas a usuários."""

    @staticmethod
    @transaction.atomic
    def criar_usuario(
        username: str,
        email: str,
        password: str,
        empresa: Empresa,
        papel: str = PapelUsuario.COLABORADOR,
        vinculo: str = VinculoUsuario.INTERNO,
        first_name: str = "",
        last_name: str = "",
        matricula: str = "",
    ) -> Usuario:
        """
        Cria um novo usuário vinculado a uma empresa.
        
        Args:
            username: Nome de usuário único
            email: Email do usuário
            password: Senha em texto plano (será hasheada)
            empresa: Empresa à qual o usuário pertence
            papel: Papel do usuário no sistema
            vinculo: Tipo de vínculo com a empresa
            first_name: Nome
            last_name: Sobrenome
            matricula: Matrícula do funcionário
            
        Returns:
            Usuario criado
            
        Raises:
            RegraDeNegocioViolada: Se username já existe ou empresa inativa
        """
        # Validar empresa ativa
        if not empresa.ativa:
            raise RegraDeNegocioViolada(
                "Não é possível criar usuários para empresas inativas."
            )

        # Validar username único
        if Usuario.objects.filter(username=username).exists():
            raise RegraDeNegocioViolada(
                f"O nome de usuário '{username}' já está em uso."
            )

        # Criar usuário
        usuario = Usuario.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            empresa=empresa,
            papel=papel,
            vinculo=vinculo,
            first_name=first_name,
            last_name=last_name,
            matricula=matricula,
            ativo=True,
            is_active=True,
            is_staff=papel in (PapelUsuario.ADMINISTRADOR, PapelUsuario.SUPERUSUARIO),
            is_superuser=papel == PapelUsuario.SUPERUSUARIO,
        )

        return usuario

    @staticmethod
    def desativar_usuario(usuario: Usuario) -> None:
        """
        Desativa um usuário (soft delete).
        Usuário não pode mais fazer login.
        """
        usuario.ativo = False
        usuario.is_active = False
        usuario.save(update_fields=["ativo", "is_active", "atualizado_em"])

    @staticmethod
    def reativar_usuario(usuario: Usuario) -> None:
        """Reativa um usuário previamente desativado."""
        usuario.ativo = True
        usuario.is_active = True
        usuario.save(update_fields=["ativo", "is_active", "atualizado_em"])

    @staticmethod
    @transaction.atomic
    def alterar_papel(usuario: Usuario, novo_papel: str) -> None:
        """
        Altera o papel de um usuário no sistema.
        Ajusta automaticamente as permissões is_staff e is_superuser.
        """
        usuario.papel = novo_papel
        usuario.is_staff = novo_papel in (
            PapelUsuario.ADMINISTRADOR,
            PapelUsuario.SUPERUSUARIO,
        )
        usuario.is_superuser = novo_papel == PapelUsuario.SUPERUSUARIO
        usuario.save(update_fields=["papel", "is_staff", "is_superuser", "atualizado_em"])