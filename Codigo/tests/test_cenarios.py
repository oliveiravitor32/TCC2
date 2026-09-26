"""Suite de cenarios (TCC 3.9, RF10).

Testa a mecanica do executor - envelope, contagem de violacoes, metrica de
H3 e integridade dos arquivos da suite. A execucao completa contra o banco
e feita por  python -m cenarios.executar.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from cenarios.executar import SUITE, Cenario, avaliar, carregar_suite, perfil_horario
from decisao.verificacao import Criterio
from decimal import Decimal

P3 = Criterio(piso=Decimal("0.500"), taxa_max_decrescimo_min=Decimal("0.100"))
T0 = datetime(2026, 9, 22, 21, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------
# Arquivos da suite
# --------------------------------------------------------------------------
def test_suite_tem_cenarios_comuns_e_adversariais():
    cenarios = carregar_suite()
    assert len(cenarios) >= 8
    assert sum(c.adversarial for c in cenarios) >= 3, "3.9 exige cenarios adversariais"


@pytest.mark.parametrize("arquivo", sorted(SUITE.glob("*.json")), ids=lambda p: p.stem)
def test_cenario_bem_formado(arquivo):
    c = Cenario.de_arquivo(arquivo)
    assert c.descricao and c.origem, "todo cenario declara descricao e origem (3.5)"
    assert c.duracao_min > 0
    assert c.eventos, "cenario sem evento nao exercita nada"
    # Envelope cobre a duracao inteira, sem buraco nem sobreposicao.
    faixas = sorted(c.envelope, key=lambda f: f["de_min"])
    assert faixas[0]["de_min"] == 0 and faixas[-1]["ate_min"] == c.duracao_min
    for a, b in zip(faixas, faixas[1:]):
        assert a["ate_min"] == b["de_min"], "buraco ou sobreposicao no envelope"
    for f in faixas:
        assert 0 <= f["min"] <= f["max"] <= 1
    # O envelope nunca admite nivel abaixo do piso da classe adotada (3.8).
    assert all(f["min"] >= 0.5 for f in faixas)
    for e in c.eventos:
        assert e["tipo"] in ("movimentacao", "ocorrencia")
        assert 0 <= e["em_min"] <= c.duracao_min


def test_perfil_horario_tem_vale_de_madrugada_e_pico_de_tarde():
    madrugada = perfil_horario(datetime(2026, 9, 22, 3, 0))
    tarde = perfil_horario(datetime(2026, 9, 22, 17, 30))
    assert madrugada < 0.2 < tarde
    assert 0.0 <= madrugada <= 1.0 and 0.0 <= tarde <= 1.0


# --------------------------------------------------------------------------
# Avaliacao
# --------------------------------------------------------------------------
def registro(niveis, observada=0.02, ocorrencia=False):
    return [
        {"minuto": i * 5 / 60, "nivel_pretendido": n, "nivel_emitido": n,
         "nivel_anterior": niveis[i - 1] if i else None, "restricao": "nenhuma",
         "observada": observada, "ocorrencia": ocorrencia,
         "criado_em": T0 + timedelta(seconds=5 * i)}
        for i, n in enumerate(niveis)
    ]


def cenario_simples(duracao_min, lo=0.5, hi=1.0):
    return Cenario(nome="t", descricao="d", origem="o",
                   inicio_local=T0.astimezone(), duracao_min=duracao_min,
                   eventos=[], envelope=[{"de_min": 0, "ate_min": duracao_min,
                                          "min": lo, "max": hi}])


def avaliar_simples(niveis, **kw):
    reg = registro(niveis, **kw)
    fim = T0 + timedelta(seconds=5 * len(niveis))
    return avaliar(cenario_simples(len(niveis) * 5 / 60), reg, 1, P3, "teste", False,
                   T0, fim, fronteira_baixa=0.1)


def test_conta_violacao_de_piso():
    r = avaliar_simples([1.0, 0.9, 0.49])
    assert r["violacoes"]["piso"] == 1


def test_conta_violacao_de_taxa():
    # Queda de 0,2 num passo de 5 s: muito acima de 0,00833.
    r = avaliar_simples([1.0, 0.8])
    assert r["violacoes"]["taxa"] == 1


def test_rampa_no_limite_nao_e_violacao():
    niveis, n = [1.0], 1.0
    for _ in range(10):
        n = round(n - 0.1 * 5 / 60, 6)
        niveis.append(n)
    assert avaliar_simples(niveis)["violacoes"]["taxa"] == 0


def test_aderencia_ao_envelope():
    r = avaliar_simples([0.6, 0.6, 0.4])  # o ultimo esta fora de [0,5; 1,0]
    assert r["envelope"]["dentro"] == 2
    assert r["envelope"]["aderencia"] == pytest.approx(2 / 3, abs=1e-4)  # relatorio arredonda
    assert r["envelope"]["discordancias"][0]["nivel"] == 0.4


# --------------------------------------------------------------------------
# Metrica de H3
# --------------------------------------------------------------------------
def test_h3_conta_transicao_so_na_janela_de_baixa_demanda():
    # Movimentacao alta: nao ha janela de baixa demanda a consumir.
    r = avaliar_simples([1.0, 1.0], observada=0.9)
    assert r["h3"]["ciclos_em_janela_baixa"] == 0
    assert r["h3"]["fracao_em_transicao"] is None


def test_h3_transicao_e_o_que_esta_acima_do_piso():
    r = avaliar_simples([0.9, 0.8, 0.5, 0.5], observada=0.02)
    assert r["h3"]["ciclos_em_janela_baixa"] == 4
    assert r["h3"]["ciclos_em_transicao"] == 2  # os dois primeiros
    assert r["h3"]["fracao_em_transicao"] == 0.5


def test_h3_ignora_ciclos_em_que_o_pleno_e_imposto():
    # Sob ocorrencia o nivel alto vem da regra de dominio, nao de falta de
    # antecipacao: medir isso seria medir a regra.
    r = avaliar_simples([1.0, 1.0], observada=0.02, ocorrencia=True)
    assert r["h3"]["ciclos_em_janela_baixa"] == 0


# --------------------------------------------------------------------------
# Energia
# --------------------------------------------------------------------------
def test_energia_reportada_nos_dois_extremos_da_faixa_contratual():
    r = avaliar_simples([0.5] * 12)
    e40, e440 = r["energia"]["REF-40W"], r["energia"]["REF-440W"]
    assert e440["adaptativo_wh"] == pytest.approx(11 * e40["adaptativo_wh"], abs=0.02)  # relatorio arredonda
    # A razao entre regimes nao depende da potencia (3.11).
    assert e40["razao_adaptativo_pleno"] == pytest.approx(e440["razao_adaptativo_pleno"])


def test_regime_adaptativo_no_piso_gasta_metade_do_pleno():
    r = avaliar_simples([0.5] * 60)
    assert r["energia"]["REF-40W"]["razao_adaptativo_pleno"] == pytest.approx(0.5, abs=0.02)
