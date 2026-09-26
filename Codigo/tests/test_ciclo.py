"""Ciclo de decisao contra o Postgres (passo 5).

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


def evento(conn, tipo, *, em, valor=None, rotulo=None, vigente_ate=None, origem="teste") -> int:
    return conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, valor, rotulo, origem, vigente_ate)"
        " VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (em, tipo, valor, rotulo, origem, vigente_ate),
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
def test_sem_dado_de_movimentacao_decide_pleno(conn, ponto):
    d = decidir(conn, ponto, T0)
    assert d.estado.observada is None
    assert d.nivel_pretendido == Decimal("1.000") and d.nivel_emitido == Decimal("1.000")


def test_movimentacao_baixa_na_madrugada_vai_ao_piso(conn, ponto):
    ev = evento(conn, "movimentacao", em=T0 - timedelta(minutes=1), valor=0.02)
    d = decidir(conn, ponto, T0)
    assert d.nivel_pretendido < Decimal("0.5")
    assert d.nivel_emitido == Decimal("0.500") and d.restricao_aplicada == "piso"
    ligados = conn.execute(
        "SELECT evento_id FROM decisao_evento WHERE decisao_id = %s", (d.id,)
    ).fetchall()
    assert ligados == [(ev,)]


def test_descida_respeita_a_taxa_entre_ciclos(conn, ponto):
    decidir(conn, ponto, T0)  # sem dado: 1,0
    evento(conn, "movimentacao", em=T0, valor=0.02)
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.nivel_anterior == Decimal("1.000")
    assert d.nivel_emitido == Decimal("0.992") and d.restricao_aplicada == "taxa"


def test_rampa_completa_leva_pelo_menos_cinco_minutos(conn, ponto):
    decidir(conn, ponto, T0)
    evento(conn, "movimentacao", em=T0, valor=0.02)
    agora, niveis = T0, []
    for _ in range(80):  # 80 x 5 s = 6 min 40 s
        agora += timedelta(seconds=5)
        niveis.append(decidir(conn, ponto, agora).nivel_emitido)
    primeiro_no_piso = niveis.index(Decimal("0.500"))
    assert (primeiro_no_piso + 1) * 5 >= 300
    assert all(a - b <= Decimal("0.0084") for a, b in zip(niveis, niveis[1:]))


def test_apos_failsafe_a_rampa_recomeca_do_pleno(conn, ponto):
    # Servico estava parado: ultima decisao (0,5) ha 60 s, mais que o timeout.
    evento(conn, "movimentacao", em=T0, valor=0.02)
    for s in range(0, 400, 5):
        decidir(conn, ponto, T0 + timedelta(seconds=s))
    volta = T0 + timedelta(seconds=395 + 60)
    d = decidir(conn, ponto, volta)
    assert d.nivel_anterior == Decimal("1.000")
    assert d.nivel_emitido == Decimal("0.992")  # e nao 0,5 de uma vez


def test_ocorrencia_eleva_e_encerrada_libera_em_rampa(conn, ponto):
    evento(conn, "movimentacao", em=T0, valor=0.02, vigente_ate=T0 + timedelta(hours=1))
    evento(conn, "ocorrencia", em=T0, rotulo="seguranca")
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.estado.ocorrencia
    assert d.nivel_emitido > Decimal("0.9")  # R1: pleno, sem diluicao
    elevado = d.nivel_emitido
    evento(conn, "ocorrencia", em=T0 + timedelta(seconds=6), rotulo="encerrada")
    d = decidir(conn, ponto, T0 + timedelta(seconds=10))
    assert not d.estado.ocorrencia
    assert d.nivel_emitido == elevado - Decimal("0.008")  # volta a descer, em rampa


def test_ocorrencia_persiste_ate_encerrada(conn, ponto):
    evento(conn, "movimentacao", em=T0, valor=0.02, vigente_ate=T0 + timedelta(hours=2))
    evento(conn, "ocorrencia", em=T0, rotulo="seguranca")
    assert ciclo.estado_via(conn, T0 + timedelta(hours=1)).ocorrencia
    evento(conn, "ocorrencia", em=T0 + timedelta(hours=1, seconds=1), rotulo="encerrada")
    assert not ciclo.estado_via(conn, T0 + timedelta(hours=1, seconds=2)).ocorrencia


def test_movimentacao_sem_vigencia_expira(conn, ponto):
    evento(conn, "movimentacao", em=T0, valor=0.02)
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=config.VALIDADE_MOVIMENTACAO_S - 1)).observada == 0.02
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=config.VALIDADE_MOVIMENTACAO_S + 1)).observada is None


def test_evento_futuro_nao_entra(conn, ponto):
    evento(conn, "ocorrencia", em=T0 + timedelta(minutes=5), rotulo="seguranca")
    assert not ciclo.estado_via(conn, T0).ocorrencia


def test_modo_reativo_nao_grava_previsao(conn, ponto):
    evento(conn, "movimentacao", em=T0, valor=0.4)
    d = decidir(conn, ponto, T0, reativo=True)
    prev = conn.execute(
        "SELECT previsao_movimentacao FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()[0]
    assert prev is None


def test_historico_horario_agrega_por_hora(conn, ponto):
    # Agrupamento por hora de relogio (T0 = 04:00 UTC). Duas leituras na
    # mesma hora viram media; a hora sem evento nao aparece, e a hora em
    # curso (incompleta) tambem nao.
    evento(conn, "movimentacao", em=T0 - timedelta(minutes=70), valor=0.2)   # 02:50 -> 2
    evento(conn, "movimentacao", em=T0 - timedelta(minutes=100), valor=0.4)  # 02:20 -> 2
    evento(conn, "movimentacao", em=T0 - timedelta(hours=3), valor=0.8)      # 01:00 -> 3
    evento(conn, "movimentacao", em=T0, valor=0.02)                           # hora em curso
    h = ciclo.historico_horario(conn, T0, horas=24)
    assert h[2] == pytest.approx(0.3)   # media de 0,2 e 0,4
    assert h[3] == pytest.approx(0.8)
    assert 1 not in h and 0 not in h


def test_previsao_do_modelo_e_gravada(conn, ponto):
    # Previsor de teste: usa o historico, para conferir que ele chega inteiro.
    class Media:
        rotulo = "persistencia"

        def horas_necessarias(self) -> int:
            return 24

        def prever(self, h: Historico) -> float:
            return sum(h.serie.values()) / len(h.serie)

    for k in range(1, 25):
        evento(conn, "movimentacao", em=T0 - timedelta(hours=k), valor=0.4)
    evento(conn, "movimentacao", em=T0, valor=0.9)
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
    # "movimentacao observada" de outra.
    evento(conn, "movimentacao", em=T0, valor=0.7, origem="cenario-historico:1",
           vigente_ate=T0 + timedelta(hours=1))
    evento(conn, "movimentacao", em=T0 - timedelta(hours=2), valor=0.7, origem="cenario:1")
    origens = ciclo.origens_da_execucao(2)
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1), origens=origens).observada is None
    assert ciclo.historico_horario(conn, T0 + timedelta(minutes=1), 24, origens) == {}
    # Em operacao (sem execucao) todas as origens valem.
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1)).observada == 0.7
