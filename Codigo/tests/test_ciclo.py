"""Ciclo de decisao contra o Postgres (passo 5; leitura por presenca, item 55).

Cada teste roda numa transacao desfeita ao final e comeca com as tabelas de
movimento vazias (o DELETE tambem e desfeito). Sem banco, os testes pulam.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg
import pytest

from decisao import ciclo, config
from decisao.inferencia import carregar
from decisao.previsao import Historico, Persistencia

try:
    psycopg.connect(config.DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)

BASE = carregar()
# 04:00 UTC = 01:00 em Sao Paulo: madrugada.
T0 = datetime(2031, 3, 10, 4, 0, tzinfo=timezone.utc)
UMA_HORA = timedelta(hours=1)

# Trechos reais do recorte do Jardim Helena (db/seed_cadastro.sql).
ANTONIO_VIANA = 20159      # trecho principal de BANCADA-01 (5,6 m)
ASCENSO_FERNANDES = 22661  # tambem de BANCADA-01 (16,5 m): poste perto da esquina
VARZEA_DA_PALMA = 19400    # so de SIMULADO-02
VINHAIS = 18570            # nenhum ponto com no


@pytest.fixture
def conn():
    c = psycopg.connect(config.DATABASE_URL)
    for t in ("alerta_diagnostico", "telemetria", "decisao_evento", "decisao",
              "calibracao", "sessao_medicao", "evento_urbano"):
        c.execute(f"DELETE FROM {t}")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture
def ponto(conn):
    return next(p for p in ciclo.pontos(conn) if p.codigo == "BANCADA-01")


@pytest.fixture
def simulado(conn):
    return next(p for p in ciclo.pontos(conn) if p.codigo == "SIMULADO-02")


def leitura(conn, *, em, pessoas=0, ocorrencia=None, vigente_ate=None, origem="teste",
            trecho=ANTONIO_VIANA) -> int:
    """Leitura do trecho: pessoas na area e ocorrencia em curso."""
    return conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, pessoas, ocorrencia, origem, trecho_id, vigente_ate)"
        " VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (em, pessoas, ocorrencia, origem, trecho, vigente_ate),
    ).fetchone()[0]


def decidir(conn, ponto, agora, **kw):
    return ciclo.decidir(
        conn,
        base=BASE,
        previsor=Persistencia(),
        ponto=ponto,
        agora=agora,
        versao_regras_id=ciclo.registrar_versao_regras(conn, BASE),
        versao_modelo_id=ciclo.id_modelo(conn, "persistencia"),
        **kw,
    )


# --------------------------------------------------------------------------
# Referencias lidas do banco
# --------------------------------------------------------------------------
def test_criterio_de_p3_vem_da_tabela(conn):
    c = ciclo.criterio(conn, "P3")
    assert c.piso == Decimal("0.5") and c.taxa_max_decrescimo_min == Decimal("0.100")


def test_classe_nao_dimerizavel_tem_piso_pleno(conn):
    assert ciclo.criterio(conn, "P6").piso == Decimal("1")


def test_hash_da_base_e_gravado_e_conferido(conn):
    vid = ciclo.registrar_versao_regras(conn, BASE)
    assert conn.execute(
        "SELECT hash_regras FROM versao_base_regras WHERE id = %s", (vid,)
    ).fetchone()[0] == BASE.hash_regras
    with pytest.raises(ciclo.BaseRegrasAlterada):
        ciclo.registrar_versao_regras(conn, replace(BASE, hash_regras="outro"))


# --------------------------------------------------------------------------
# Decisoes
# --------------------------------------------------------------------------
def test_sem_leitura_decide_pleno(conn, ponto):
    d = decidir(conn, ponto, T0)
    assert d.estado.sem_dado
    assert d.nivel_pretendido == Decimal("1.000") and d.nivel_emitido == Decimal("1.000")


def test_via_vazia_de_madrugada_vai_ao_piso(conn, ponto):
    ev = leitura(conn, em=T0 - timedelta(seconds=10))
    d = decidir(conn, ponto, T0)
    assert not d.estado.presenca
    assert d.nivel_pretendido < Decimal("0.5")
    assert d.nivel_emitido == Decimal("0.500") and d.restricao_aplicada == "piso"
    ligados = conn.execute(
        "SELECT evento_id FROM decisao_evento WHERE decisao_id = %s", (d.id,)
    ).fetchall()
    assert ligados == [(ev,)]


@pytest.mark.parametrize("pessoas", [1, 2, 30])
def test_uma_pessoa_ja_leva_ao_pleno(conn, ponto, pessoas):
    leitura(conn, em=T0, pessoas=pessoas)
    d = decidir(conn, ponto, T0 + timedelta(seconds=1))
    assert d.estado.presenca and d.nivel_emitido > Decimal("0.9")


def test_descida_respeita_a_taxa_entre_ciclos(conn, ponto):
    decidir(conn, ponto, T0)  # sem dado: 1,0
    leitura(conn, em=T0, vigente_ate=T0 + UMA_HORA)
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.nivel_anterior == Decimal("1.000")
    assert d.nivel_emitido == Decimal("0.992") and d.restricao_aplicada == "taxa"


def test_rampa_completa_leva_pelo_menos_cinco_minutos(conn, ponto):
    decidir(conn, ponto, T0)
    leitura(conn, em=T0, vigente_ate=T0 + UMA_HORA)
    agora, niveis = T0, []
    for _ in range(80):  # 80 x 5 s = 6 min 40 s
        agora += timedelta(seconds=5)
        niveis.append(decidir(conn, ponto, agora).nivel_emitido)
    primeiro_no_piso = niveis.index(Decimal("0.500"))
    assert (primeiro_no_piso + 1) * 5 >= 300
    assert all(a - b <= Decimal("0.0084") for a, b in zip(niveis, niveis[1:]))


def test_pedestre_eleva_na_hora_e_a_saida_libera_em_rampa(conn, ponto):
    leitura(conn, em=T0, vigente_ate=T0 + UMA_HORA)
    for s in range(0, 400, 5):
        decidir(conn, ponto, T0 + timedelta(seconds=s))  # desce ao piso
    leitura(conn, em=T0 + timedelta(seconds=401), pessoas=1)
    d = decidir(conn, ponto, T0 + timedelta(seconds=405))
    assert d.nivel_emitido > Decimal("0.9")  # elevacao imediata, sem limite de taxa
    elevado = d.nivel_emitido
    leitura(conn, em=T0 + timedelta(seconds=406), pessoas=0, vigente_ate=T0 + UMA_HORA)
    d = decidir(conn, ponto, T0 + timedelta(seconds=410))
    assert d.nivel_emitido == elevado - Decimal("0.008")  # volta a descer, em rampa


def test_apos_failsafe_a_rampa_recomeca_do_pleno(conn, ponto):
    # Servico estava parado: ultima decisao (0,5) ha 60 s, mais que o timeout.
    leitura(conn, em=T0, vigente_ate=T0 + UMA_HORA)
    for s in range(0, 400, 5):
        decidir(conn, ponto, T0 + timedelta(seconds=s))
    volta = T0 + timedelta(seconds=395 + 60)
    d = decidir(conn, ponto, volta)
    assert d.nivel_anterior == Decimal("1.000")
    assert d.nivel_emitido == Decimal("0.992")  # e nao 0,5 de uma vez


def test_ocorrencia_com_via_vazia_eleva(conn, ponto):
    leitura(conn, em=T0, ocorrencia="seguranca")
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.estado.ocorrencia and not d.estado.presenca
    assert d.nivel_emitido > Decimal("0.9")  # R1: pleno, sem diluicao


def test_leitura_sem_vigencia_expira(conn, ponto):
    leitura(conn, em=T0, pessoas=2)
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=config.VALIDADE_LEITURA_S - 1), ponto_id=ponto.id).presenca
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=config.VALIDADE_LEITURA_S + 1), ponto_id=ponto.id).sem_dado


def test_leitura_mais_recente_do_trecho_prevalece(conn, ponto):
    leitura(conn, em=T0, pessoas=3)
    leitura(conn, em=T0 + timedelta(seconds=5), pessoas=0)
    e = ciclo.estado_via(conn, T0 + timedelta(seconds=6), ponto_id=ponto.id)
    assert not e.presenca and e.pessoas == {ANTONIO_VIANA: 0}


def test_leitura_futura_nao_entra(conn, ponto):
    leitura(conn, em=T0 + timedelta(minutes=5), ocorrencia="seguranca")
    assert ciclo.estado_via(conn, T0, ponto_id=ponto.id).sem_dado


def test_modo_reativo_nao_grava_previsao(conn, ponto):
    leitura(conn, em=T0, pessoas=0)
    d = decidir(conn, ponto, T0, reativo=True)
    prev = conn.execute(
        "SELECT previsao_movimentacao FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()[0]
    assert prev is None


def test_decisao_grava_o_porque(conn, ponto):
    leitura(conn, em=T0, pessoas=2, ocorrencia="transito")
    d = decidir(conn, ponto, T0 + timedelta(seconds=1))
    entrada, ativacoes = conn.execute(
        "SELECT entrada, ativacoes FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()
    assert entrada["presenca"] and entrada["ocorrencia"]
    assert entrada["pessoas_por_trecho"] == {str(ANTONIO_VIANA): 2}
    assert ativacoes["R1"] == 1.0 and ativacoes["R2"] == 1.0 and ativacoes["R4"] == 0.0


# --------------------------------------------------------------------------
# Serie para a previsao (normalizada por trecho, 3.6)
# --------------------------------------------------------------------------
def test_historico_horario_normaliza_pela_referencia_do_trecho(conn, ponto):
    # Referencia inicial do trecho = 5 pessoas (trecho_via.referencia_pessoas).
    # Duas leituras na mesma hora viram media; a hora em curso nao entra.
    leitura(conn, em=T0 - timedelta(minutes=70), pessoas=1)   # 02:50 -> atraso 2
    leitura(conn, em=T0 - timedelta(minutes=100), pessoas=3)  # 02:20 -> atraso 2
    leitura(conn, em=T0 - timedelta(hours=3), pessoas=8)      # 01:00 -> atraso 3 (satura)
    leitura(conn, em=T0, pessoas=0)                           # hora em curso
    h = ciclo.historico_horario(conn, T0, horas=24, ponto_id=ponto.id)
    assert h[2] == pytest.approx(2 / 5)
    assert h[3] == pytest.approx(1.0)
    assert 1 not in h and 0 not in h


def test_referencia_e_aprendida_com_historico_suficiente(conn, ponto):
    # 168 horas com media de 2 pessoas: a referencia aprendida e 2, e nao 5.
    for k in range(1, 170):
        leitura(conn, em=T0 - timedelta(hours=k), pessoas=2)
    refs = ciclo.referencias(conn, T0, ponto.id)
    assert refs[ANTONIO_VIANA] == pytest.approx(2.0)
    assert refs[ASCENSO_FERNANDES] == pytest.approx(5.0)  # sem historico: valor inicial


def test_previsao_do_modelo_e_gravada(conn, ponto):
    # Previsor de teste: usa o historico, para conferir que ele chega inteiro.
    class Media:
        rotulo = "persistencia"

        def horas_necessarias(self) -> int:
            return 24

        def prever(self, h: Historico) -> float:
            return sum(h.serie.values()) / len(h.serie)

    for k in range(1, 25):
        leitura(conn, em=T0 - timedelta(hours=k), pessoas=2)  # 2/5 = 0,4
    leitura(conn, em=T0, pessoas=0)
    d = ciclo.decidir(
        conn, base=BASE, previsor=Media(), ponto=ponto, agora=T0,
        versao_regras_id=ciclo.registrar_versao_regras(conn, BASE),
        versao_modelo_id=ciclo.id_modelo(conn, "persistencia"),
    )
    gravada = conn.execute(
        "SELECT previsao_movimentacao FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()[0]
    assert float(gravada) == pytest.approx(0.4, abs=0.001)


# --------------------------------------------------------------------------
# Telemetria e estado do no
# --------------------------------------------------------------------------
def _carga(d, **kw):
    return {"decisao_id": str(d.id), "duty": 0.25, "lux": 5.2,
            "medido_em": (T0 + timedelta(seconds=1)).isoformat(), **kw}


def test_telemetria_e_gravada_uma_vez_so(conn, ponto):
    d = decidir(conn, ponto, T0)
    assert ciclo.registrar_telemetria(conn, "BANCADA-01", _carga(d))
    assert not ciclo.registrar_telemetria(conn, "BANCADA-01", _carga(d))  # reentrega QoS 1
    n = conn.execute("SELECT count(*) FROM telemetria WHERE decisao_id = %s", (d.id,)).fetchone()[0]
    assert n == 1


@pytest.mark.parametrize(
    "ponto_msg,extra",
    [("OUTRO-PONTO", {}), ("BANCADA-01", {"duty": 1.5}), ("BANCADA-01", {"lux": -1}),
     ("BANCADA-01", {"decisao_id": "nao-e-uuid"})],
)
def test_telemetria_invalida_e_descartada(conn, ponto, ponto_msg, extra):
    d = decidir(conn, ponto, T0)
    assert not ciclo.registrar_telemetria(conn, ponto_msg, _carga(d, **extra))


def test_telemetria_liga_a_sessao_aberta(conn, ponto):
    sid = conn.execute(
        "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe)"
        " VALUES (%s, 0.3, 10) RETURNING id", (ponto.id,)
    ).fetchone()[0]
    d = decidir(conn, ponto, T0)
    ciclo.registrar_telemetria(conn, "BANCADA-01", _carga(d))
    assert conn.execute(
        "SELECT sessao_id FROM telemetria WHERE decisao_id = %s", (d.id,)
    ).fetchone()[0] == sid


def test_last_will_marca_sem_comunicacao(conn, ponto):
    ciclo.atualizar_estado_ponto(conn, "BANCADA-01", online=False)
    estado = lambda: conn.execute(
        "SELECT estado_operacional FROM ponto_de_luz WHERE id = %s", (ponto.id,)
    ).fetchone()[0]
    assert estado() == "sem_comunicacao"
    ciclo.atualizar_estado_ponto(conn, "BANCADA-01", online=True)
    assert estado() == "operante"


def test_execucao_de_cenario_so_enxerga_os_proprios_eventos(conn, ponto):
    # DIVERGENCIAS 51: o historico sintetico de uma execucao nao pode virar
    # leitura de outra.
    leitura(conn, em=T0, pessoas=3, origem="cenario-historico:1", vigente_ate=T0 + UMA_HORA)
    leitura(conn, em=T0 - timedelta(hours=2), pessoas=3, origem="cenario:1")
    origens = ciclo.origens_da_execucao(2)
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1), origens=origens, ponto_id=ponto.id).sem_dado
    assert ciclo.historico_horario(conn, T0 + timedelta(minutes=1), 24, origens, ponto_id=ponto.id) == {}
    # Em operacao (sem execucao) todas as origens valem.
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1), ponto_id=ponto.id).presenca


# --------------------------------------------------------------------------
# Associacao espacial trecho x ponto (DIVERGENCIAS 54)
# --------------------------------------------------------------------------
def test_leitura_de_outro_trecho_nao_afeta_o_ponto(conn, ponto, simulado):
    leitura(conn, em=T0, ocorrencia="seguranca", trecho=VARZEA_DA_PALMA)
    assert ciclo.estado_via(conn, T0, ponto_id=simulado.id).ocorrencia
    assert ciclo.estado_via(conn, T0, ponto_id=ponto.id).sem_dado


def test_poste_perto_da_esquina_responde_aos_dois_trechos(conn, ponto):
    leitura(conn, em=T0, pessoas=1, trecho=ASCENSO_FERNANDES)
    assert ciclo.estado_via(conn, T0, ponto_id=ponto.id).presenca


def test_basta_um_trecho_com_pedestre(conn, ponto):
    leitura(conn, em=T0, pessoas=0, trecho=ANTONIO_VIANA)
    leitura(conn, em=T0, pessoas=1, trecho=ASCENSO_FERNANDES)
    e = ciclo.estado_via(conn, T0 + timedelta(seconds=1), ponto_id=ponto.id)
    assert e.presenca
    assert e.pessoas == {ANTONIO_VIANA: 0, ASCENSO_FERNANDES: 1}
    assert len(e.evento_ids) == 2  # a auditoria registra os dois trechos


def test_ocorrencia_num_trecho_vale_mesmo_com_outro_sem(conn, ponto):
    leitura(conn, em=T0, ocorrencia=None, trecho=ANTONIO_VIANA)
    leitura(conn, em=T0, ocorrencia="seguranca", trecho=ASCENSO_FERNANDES)
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=1), ponto_id=ponto.id).ocorrencia


def test_trecho_sem_ponto_nao_gera_estado(conn, ponto, simulado):
    leitura(conn, em=T0, ocorrencia="seguranca", trecho=VINHAIS)
    for p in (ponto, simulado):
        assert ciclo.estado_via(conn, T0, ponto_id=p.id).sem_dado


def test_decisoes_independentes_por_ponto(conn, ponto, simulado):
    # A mesma rodada decide cada ponto pelo proprio trecho: a Varzea da Palma
    # vazia desce, a Antonio Viana com pedestre fica no pleno.
    leitura(conn, em=T0, pessoas=0, trecho=VARZEA_DA_PALMA, vigente_ate=T0 + UMA_HORA)
    leitura(conn, em=T0, pessoas=1, trecho=ANTONIO_VIANA, vigente_ate=T0 + UMA_HORA)
    for k in range(1, 13):
        agora = T0 + timedelta(seconds=5 * k)
        a = decidir(conn, ponto, agora)
        b = decidir(conn, simulado, agora)
    assert a.estado.presenca and a.nivel_emitido > Decimal("0.9")
    assert not b.estado.presenca and b.nivel_emitido == Decimal("0.500")  # piso
