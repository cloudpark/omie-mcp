"""Testes da política de escrita e da exigência de identificadores.

O que estes testes protegem: a garantia de que uma tool mutante não autorizada
não chega a existir no schema MCP. É uma propriedade de segurança, não uma
conveniência — se alguém registrar uma tool fora do bloco de policy, o teste de
contagem quebra.
"""

import asyncio

import pytest
from mcp.server.fastmcp import FastMCP

from omie_mcp.client import exigir_identificador
from omie_mcp.policy import WritePolicy
from omie_mcp.tools import (
    bancos,
    categorias,
    contas_correntes,
    contas_pagar,
    contas_receber,
    dre,
    fluxo_caixa,
    fornecedores,
    lancamentos_cc,
    tipos_documento,
)

MODULOS = (
    fornecedores,
    contas_pagar,
    contas_receber,
    lancamentos_cc,
    contas_correntes,
    fluxo_caixa,
    categorias,
    dre,
    tipos_documento,
    bancos,
)

# Tools que gravam no ERP, por nível mínimo de autorização.
ESCRITA = {
    "incluir_fornecedor",
    "alterar_fornecedor",
    "incluir_conta_pagar",
    "lancar_pagamento",
    "incluir_conta_receber",
    "lancar_recebimento",
    "incluir_lancamento_bancario",
    "incluir_categoria",
    "alterar_categoria",
    "incluir_grupo_categoria",
    "alterar_grupo_categoria",
}
DESTRUTIVA = {
    "excluir_conta_pagar",
    "cancelar_pagamento_conta_pagar",
    "excluir_conta_receber",
    "cancelar_recebimento",
    "excluir_lancamento_bancario",
}


def tools_registradas(modo: str) -> set[str]:
    mcp = FastMCP(name="teste")
    policy = WritePolicy(modo)
    for modulo in MODULOS:
        modulo.register(mcp, policy)
    return {t.name for t in asyncio.run(mcp.list_tools())}


def test_modo_off_e_o_padrao():
    assert WritePolicy(None).modo == "off"
    assert WritePolicy.do_ambiente({}).modo == "off"


@pytest.mark.parametrize("modo,total", [("off", 25), ("on", 36), ("all", 41)])
def test_total_de_tools_por_modo(modo, total):
    assert len(tools_registradas(modo)) == total


def test_off_nao_registra_nenhuma_escrita():
    registradas = tools_registradas("off")
    assert not registradas & (ESCRITA | DESTRUTIVA)


def test_on_registra_escrita_mas_nao_destrutiva():
    registradas = tools_registradas("on")
    assert ESCRITA <= registradas
    assert not registradas & DESTRUTIVA


def test_all_registra_tudo():
    registradas = tools_registradas("all")
    assert (ESCRITA | DESTRUTIVA) <= registradas


# Os testes acima checam contagem e contenção; os dois abaixo pinam a
# classificação exata. Importam porque o gate é posicional: cada módulo faz
# `if not policy.escrita: return` e segue definindo tools. Uma tool destrutiva
# escrita acima daquele guard passaria a existir no modo `on`, e é isto que
# quebra aqui — com o nome da tool na mensagem, não só "36 != 37".


def test_on_libera_exatamente_o_conjunto_de_escrita():
    assert tools_registradas("on") - tools_registradas("off") == ESCRITA


def test_all_libera_exatamente_o_conjunto_destrutivo():
    assert tools_registradas("all") - tools_registradas("on") == DESTRUTIVA


def test_modo_invalido_falha_fechado():
    # Um valor não reconhecido não pode virar silenciosamente "all" nem "off".
    for invalido in ("readonly", "true", "write", "ALL_TOOLS"):
        with pytest.raises(ValueError, match="OMIE_WRITE_MODE"):
            WritePolicy(invalido)


def test_modo_aceita_espaco_e_maiuscula():
    assert WritePolicy(" ALL ").modo == "all"


def test_exigir_identificador_recusa_params_vazio():
    with pytest.raises(ValueError, match="ao menos um identificador"):
        exigir_identificador({}, "codigo_a ou codigo_b")


def test_exigir_identificador_aceita_codigo_zero():
    # Um código 0 é um identificador informado, não ausência de identificador.
    params = {"codigo_a": 0}
    assert exigir_identificador(params, "codigo_a ou codigo_b") is params
