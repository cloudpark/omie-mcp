"""Política de escrita — decide quais ferramentas mutantes chegam a existir.

O servidor nasce somente leitura. As ferramentas que gravam no ERP só entram no
schema MCP se OMIE_WRITE_MODE autorizar, e a diferença importa: o que não é
registrado não aparece na lista de tools, não entra no contexto do modelo e não
pode ser invocado por texto que veio de dentro do próprio ERP (o campo
`observacao` de um título, o nome de um fornecedor). Uma tool que existe e
recusa ainda se anuncia; uma que não existe, não.

    OMIE_WRITE_MODE=off   (padrão)  somente leitura — 25 tools
    OMIE_WRITE_MODE=on              + criar/editar/baixar — 11 tools
    OMIE_WRITE_MODE=all             + excluir/estornar — 5 tools
"""

from __future__ import annotations

import os

MODO_PADRAO = "off"
MODOS = ("off", "on", "all")

VAR_AMBIENTE = "OMIE_WRITE_MODE"


class WritePolicy:
    """Nível de escrita autorizado para esta execução do servidor."""

    def __init__(self, modo: str | None):
        normalizado = (modo or MODO_PADRAO).strip().lower()
        if normalizado not in MODOS:
            raise ValueError(
                f"{VAR_AMBIENTE} inválido: {modo!r}. "
                f"Valores aceitos: {', '.join(MODOS)}."
            )
        self.modo = normalizado

    @classmethod
    def do_ambiente(cls, ambiente: dict[str, str] | None = None) -> WritePolicy:
        env = os.environ if ambiente is None else ambiente
        return cls(env.get(VAR_AMBIENTE))

    @property
    def escrita(self) -> bool:
        """Autoriza incluir_*, alterar_* e lancar_* — cria e edita registros."""
        return self.modo in ("on", "all")

    @property
    def destrutiva(self) -> bool:
        """Autoriza excluir_* e cancelar_* — apaga títulos e estorna baixas."""
        return self.modo == "all"

    def __str__(self) -> str:
        return self.modo
