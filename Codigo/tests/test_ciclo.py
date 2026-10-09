"""Ciclo de decisao contra o Postgres (passo 5; volume e degraus de classe, item 56).

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


def volume(conn, *, em, media=0.0, periodo_s=300, vigente_ate=None, origem="teste",
           trecho=ANTONIO_VIANA) -> int:
    """Volume do trecho: media de pessoas no periodo que termina em `em`."""
    return conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id,"
        " vigente_ate) VALUES (%s, 'volume', %s, %s, %s, %s, %s) RETURNING id",
        (em, media, periodo_s, origem, trecho, vigente_ate),
    ).fetchone()[0]


def ocorrencia(conn, *, em, rotulo, vigente_ate=None, origem="teste", trecho=ANTONIO_VIANA) -> int:
    return conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, ocorrencia, origem, trecho_id, vigente_ate)"
        " VALUES (%s, 'ocorrencia', %s, %s, %s, %s) RETURNING id",
        (em, rotulo, origem, trecho, vigente_ate),
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


def test_degraus_de_classe_vem_da_tabela(conn):
    # P3 -> P4 -> P5 (10; 7,5; 5 lux): cada degrau da inferencia e uma classe.
    assert ciclo.niveis_classe(conn, "P3") == (Decimal("1"), Decimal("0.75"), Decimal("0.5"))
    um, meio, minimo = ciclo.niveis_classe(conn, "P4")  # P4 -> P5 -> P6
    assert (um, round(meio, 4), minimo) == (Decimal("1"), Decimal("0.6667"), Decimal("0.4"))
    assert minimo == ciclo.criterio(conn, "P4").piso


@pytest.mark.parametrize("classe", ["P5", "P6"])
def test_classe_sem_degraus_fica_no_pleno(conn, classe):
    assert ciclo.niveis_classe(conn, classe) == (Decimal("1.000"),) * 3


def test_hash_da_base_e_gravado_e_conferido(conn):
    vid = ciclo.registrar_versao_regras(conn, BASE)
    assert conn.execute(
        "SELECT hash_regras FROM versao_base_regras WHERE id = %s", (vid,)
    ).fetchone()[0] == BASE.hash_regras
    with pytest.raises(ciclo.BaseRegrasAlterada):
        ciclo.registrar_versao_regras(conn, replace(BASE, hash_regras="outro"))


# --------------------------------------------------------------------------
# Decisoes: volume de movimento e degraus de classe
# --------------------------------------------------------------------------
def test_sem_volume_decide_pleno(conn, ponto):
    d = decidir(conn, ponto, T0)
    assert d.estado.sem_dado
    assert d.nivel_pretendido == Decimal("1.000") and d.nivel_emitido == Decimal("1.000")


def test_volume_baixo_de_madrugada_vai_a_classe_minima(conn, ponto):
    ev = volume(conn, em=T0 - timedelta(seconds=10), media=0.02)  # 0,004 do pleno: faixa baixa
    d = decidir(conn, ponto, T0)
    assert d.nivel_pretendido == Decimal("0.500")  # P5, exatamente
    assert d.nivel_emitido == Decimal("0.500") and d.restricao_aplicada == "nenhuma"
    ligados = conn.execute(
        "SELECT evento_id FROM decisao_evento WHERE decisao_id = %s", (d.id,)
    ).fetchall()
    assert ligados == [(ev,)]


def test_uma_pessoa_em_media_nao_forca_o_pleno(conn, ponto):
    # 1 pessoa numa via de referencia 5 = 0,2: volume medio -> P4 (0,75).
    volume(conn, em=T0, media=1)
    d = decidir(conn, ponto, T0 + timedelta(seconds=1))
    assert d.nivel_emitido == Decimal("0.750")
    assert d.observada == pytest.approx(0.2)


def test_volume_alto_fica_na_classe_da_via(conn, ponto):
    volume(conn, em=T0, media=4)  # 0,8: alto
    d = decidir(conn, ponto, T0 + timedelta(seconds=1))
    assert d.nivel_emitido == Decimal("1.000") and d.degrau == pytest.approx(0.0)


def test_central_manda_o_alvo_e_a_rampa_fica_no_controlador(conn, ponto):
    # Item 71: a central verifica so o piso do alvo; a taxa de descida e
    # garantida pelo controlador (test_rampa.py), pela mesma regra.
    decidir(conn, ponto, T0)  # sem dado: 1,0
    volume(conn, em=T0, vigente_ate=T0 + UMA_HORA)
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.nivel_anterior == Decimal("1.000")
    assert d.nivel_emitido == Decimal("0.500") and d.restricao_aplicada == "nenhuma"
    cmd = d.comando()
    assert cmd["nivel"] == 0.5 and cmd["piso"] == 0.5 and cmd["taxa_min"] == 0.1


def test_validade_do_comando_acompanha_o_volume(conn, ponto):
    # Sem dado: o maximo. Com volume: ate ele vencer (15 min depois do fim
    # do periodo), nunca mais que o maximo.
    assert decidir(conn, ponto, T0).validade_s == config.VALIDADE_COMANDO_MAX_S
    volume(conn, em=T0, media=0.02)
    assert decidir(conn, ponto, T0 + timedelta(minutes=4)).validade_s == 11 * 60
    volume(conn, em=T0, media=0.02, trecho=ASCENSO_FERNANDES,
           vigente_ate=T0 + timedelta(hours=2))
    assert decidir(conn, ponto, T0 + timedelta(minutes=5)).validade_s == config.VALIDADE_COMANDO_MAX_S


def test_validade_e_gravada_e_o_ultimo_publicado_e_lido(conn, ponto):
    volume(conn, em=T0, media=0.02)
    d = decidir(conn, ponto, T0 + timedelta(minutes=1))
    assert ciclo.ultimo_publicado(conn, ponto.id) is None  # nao publicada
    ciclo.marcar_publicada(conn, d.id, T0 + timedelta(minutes=1))
    nivel, vence = ciclo.ultimo_publicado(conn, ponto.id)
    assert nivel == Decimal("0.500") and vence == T0 + timedelta(minutes=15)


def test_evento_acorda_so_os_pontos_do_trecho(conn, ponto, simulado):
    ev = volume(conn, em=T0, trecho=VARZEA_DA_PALMA)
    assert [p.codigo for p in ciclo.pontos_do_evento(conn, ev)] == ["SIMULADO-02"]
    ev = volume(conn, em=T0, trecho=VINHAIS)
    assert ciclo.pontos_do_evento(conn, ev) == []


def test_varredura_pega_so_comando_vencendo(conn, ponto, simulado):
    volume(conn, em=T0, media=0.02)
    for p in (ponto, simulado):
        ciclo.marcar_publicada(conn, decidir(conn, p, T0).id, T0)
    # BANCADA-01 vence em 15 min (volume); SIMULADO-02, sem dado, em 15 min tambem.
    cedo = {p.codigo for p in ciclo.pontos_vencendo(conn, T0 + timedelta(minutes=5), 300)}
    assert not cedo & {"BANCADA-01", "SIMULADO-02"}
    vencendo = {p.codigo for p in ciclo.pontos_vencendo(conn, T0 + timedelta(minutes=10), 300)}
    assert {"BANCADA-01", "SIMULADO-02"} <= vencendo


def test_ocorrencia_com_via_vazia_leva_a_classe_da_via(conn, ponto):
    volume(conn, em=T0)
    ocorrencia(conn, em=T0, rotulo="seguranca")
    d = decidir(conn, ponto, T0 + timedelta(seconds=5))
    assert d.estado.ocorrencia
    assert d.nivel_emitido == Decimal("1.000")  # R1, sem diluicao


def test_ocorrencia_encerrada_pela_plataforma(conn, ponto):
    ocorrencia(conn, em=T0, rotulo="seguranca")
    ocorrencia(conn, em=T0 + timedelta(minutes=2), rotulo="encerrada")
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1), ponto_id=ponto.id).ocorrencia
    assert not ciclo.estado_via(conn, T0 + timedelta(minutes=3), ponto_id=ponto.id).ocorrencia


def test_ocorrencia_vence_pelo_prazo_o_que_vier_primeiro(conn, ponto):
    ocorrencia(conn, em=T0, rotulo="transito", vigente_ate=T0 + timedelta(minutes=5))
    assert not ciclo.estado_via(conn, T0 + timedelta(minutes=6), ponto_id=ponto.id).ocorrencia
    ocorrencia(conn, em=T0 + timedelta(minutes=10), rotulo="seguranca")  # sem vigencia
    agora = T0 + timedelta(minutes=10)
    ok = timedelta(seconds=config.VALIDADE_OCORRENCIA_S - 1)
    vencida = timedelta(seconds=config.VALIDADE_OCORRENCIA_S + 1)
    assert ciclo.estado_via(conn, agora + ok, ponto_id=ponto.id).ocorrencia
    assert not ciclo.estado_via(conn, agora + vencida, ponto_id=ponto.id).ocorrencia


def test_volume_vale_tres_periodos_e_expira(conn, ponto):
    assert config.VALIDADE_VOLUME_S == 3 * config.PERIODO_VOLUME_S == 900
    volume(conn, em=T0, media=2)
    assert not ciclo.estado_via(conn, T0 + timedelta(seconds=899), ponto_id=ponto.id).sem_dado
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=901), ponto_id=ponto.id).sem_dado


def test_volume_mais_recente_do_trecho_prevalece(conn, ponto):
    volume(conn, em=T0, media=3)
    volume(conn, em=T0 + timedelta(minutes=5), media=0.5)
    e = ciclo.estado_via(conn, T0 + timedelta(minutes=6), ponto_id=ponto.id)
    assert e.volumes == {ANTONIO_VIANA: 0.5}


def test_publicacao_futura_nao_entra(conn, ponto):
    volume(conn, em=T0 + timedelta(minutes=5), media=3)
    ocorrencia(conn, em=T0 + timedelta(minutes=5), rotulo="seguranca")
    e = ciclo.estado_via(conn, T0, ponto_id=ponto.id)
    assert e.sem_dado and not e.ocorrencia


def test_modo_reativo_nao_grava_previsao(conn, ponto):
    volume(conn, em=T0)
    d = decidir(conn, ponto, T0, reativo=True)
    prev = conn.execute(
        "SELECT previsao_movimentacao FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()[0]
    assert prev is None


def test_decisao_grava_o_porque(conn, ponto):
    volume(conn, em=T0, media=2)
    ocorrencia(conn, em=T0, rotulo="transito")
    d = decidir(conn, ponto, T0 + timedelta(seconds=1))
    entrada, ativacoes = conn.execute(
        "SELECT entrada, ativacoes FROM decisao WHERE id = %s", (d.id,)
    ).fetchone()
    assert entrada["ocorrencia"]
    assert entrada["pessoas_media_por_trecho"] == {str(ANTONIO_VIANA): 2.0}
    assert entrada["observada"] == pytest.approx(0.4)
    assert entrada["niveis_classe"] == [1.0, 0.75, 0.5]
    assert entrada["degrau"] == pytest.approx(0.0)
    assert ativacoes["R1"] == 1.0 and ativacoes["R4"] == 0.0


# --------------------------------------------------------------------------
# Serie para a previsao (normalizada por trecho, 3.6)
# --------------------------------------------------------------------------
def test_historico_horario_normaliza_pela_referencia_do_trecho(conn, ponto):
    # Referencia inicial do trecho = 5 pessoas (trecho_via.referencia_pessoas).
    # Dois volumes na mesma hora viram media; a hora em curso nao entra; as
    # ocorrencias nao entram na serie.
    volume(conn, em=T0 - timedelta(minutes=70), media=1)   # 02:50 -> atraso 2
    volume(conn, em=T0 - timedelta(minutes=100), media=3)  # 02:20 -> atraso 2
    volume(conn, em=T0 - timedelta(hours=3), media=8)      # 01:00 -> atraso 3 (satura)
    ocorrencia(conn, em=T0 - timedelta(hours=4), rotulo="seguranca")
    volume(conn, em=T0, media=0)                           # hora em curso
    h = ciclo.historico_horario(conn, T0, horas=24, ponto_id=ponto.id)
    assert h[2] == pytest.approx(2 / 5)
    assert h[3] == pytest.approx(1.0)
    assert set(h) == {2, 3}


def test_referencia_e_aprendida_com_historico_suficiente(conn, ponto):
    # 7 dias de blocos de 15 min (672) com media de 2 pessoas: a referencia
    # aprendida e 2, e nao 5 (DIVERGENCIAS 69).
    for k in range(1, 675):
        volume(conn, em=T0 - timedelta(minutes=15 * k), media=2)
    assert ciclo.calcular_referencias(conn, T0, ponto.id)[ANTONIO_VIANA] == pytest.approx(2.0)
    # Em operacao, a decisao le a regua gravada pela rotina diaria (item 71):
    # antes dela, o valor inicial; depois, a aprendida.
    conn.execute("UPDATE trecho_via SET referencia_aprendida = NULL, referencia_calculada_em = NULL")
    assert ciclo.referencias(conn, T0, ponto.id)[ANTONIO_VIANA] == pytest.approx(5.0)
    assert ciclo.referencias_vencidas(conn, T0)
    ciclo.atualizar_referencias(conn, T0)
    refs = ciclo.referencias(conn, T0, ponto.id)
    assert refs[ANTONIO_VIANA] == pytest.approx(2.0)
    assert refs[ASCENSO_FERNANDES] == pytest.approx(5.0)  # sem historico: valor inicial
    assert not ciclo.referencias_vencidas(conn, T0 + timedelta(hours=23))


def test_previsao_do_modelo_e_gravada(conn, ponto):
    # Previsor de teste: usa o historico, para conferir que ele chega inteiro.
    class Media:
        rotulo = "persistencia"

        def horas_necessarias(self) -> int:
            return 24

        def prever(self, h: Historico) -> float:
            return sum(h.serie.values()) / len(h.serie)

    for k in range(1, 25):
        volume(conn, em=T0 - timedelta(hours=k), media=2)  # 2/5 = 0,4
    volume(conn, em=T0)
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
    # volume observado de outra.
    volume(conn, em=T0, media=3, origem="cenario-historico:1", vigente_ate=T0 + UMA_HORA)
    volume(conn, em=T0 - timedelta(hours=2), media=3, origem="cenario:1")
    origens = ciclo.origens_da_execucao(2)
    assert ciclo.estado_via(conn, T0 + timedelta(minutes=1), origens=origens, ponto_id=ponto.id).sem_dado
    assert ciclo.historico_horario(conn, T0 + timedelta(minutes=1), 24, origens, ponto_id=ponto.id) == {}
    # Em operacao (sem execucao) todas as origens valem.
    assert not ciclo.estado_via(conn, T0 + timedelta(minutes=1), ponto_id=ponto.id).sem_dado


# --------------------------------------------------------------------------
# Associacao espacial trecho x ponto (DIVERGENCIAS 54)
# --------------------------------------------------------------------------
def test_publicacao_de_outro_trecho_nao_afeta_o_ponto(conn, ponto, simulado):
    ocorrencia(conn, em=T0, rotulo="seguranca", trecho=VARZEA_DA_PALMA)
    volume(conn, em=T0, media=2, trecho=VARZEA_DA_PALMA)
    assert ciclo.estado_via(conn, T0, ponto_id=simulado.id).ocorrencia
    e = ciclo.estado_via(conn, T0, ponto_id=ponto.id)
    assert e.sem_dado and not e.ocorrencia


def test_poste_perto_da_esquina_responde_aos_dois_trechos(conn, ponto):
    volume(conn, em=T0, media=1, trecho=ASCENSO_FERNANDES)
    assert ciclo.estado_via(conn, T0, ponto_id=ponto.id).volumes == {ASCENSO_FERNANDES: 1.0}


def test_entre_trechos_vale_o_maior_volume(conn, ponto):
    volume(conn, em=T0, media=0, trecho=ANTONIO_VIANA)
    volume(conn, em=T0, media=4, trecho=ASCENSO_FERNANDES)
    e = ciclo.estado_via(conn, T0 + timedelta(seconds=1), ponto_id=ponto.id)
    assert e.volumes == {ANTONIO_VIANA: 0.0, ASCENSO_FERNANDES: 4.0}
    assert len(e.evento_ids) == 2  # a auditoria registra os dois trechos
    assert ciclo.observada(e, ciclo.referencias(conn, T0, ponto.id)) == pytest.approx(0.8)


def test_ocorrencia_num_trecho_vale_mesmo_com_outro_sem(conn, ponto):
    volume(conn, em=T0, trecho=ANTONIO_VIANA)
    ocorrencia(conn, em=T0, rotulo="seguranca", trecho=ASCENSO_FERNANDES)
    assert ciclo.estado_via(conn, T0 + timedelta(seconds=1), ponto_id=ponto.id).ocorrencia


def test_trecho_sem_ponto_nao_gera_estado(conn, ponto, simulado):
    ocorrencia(conn, em=T0, rotulo="seguranca", trecho=VINHAIS)
    volume(conn, em=T0, media=3, trecho=VINHAIS)
    for p in (ponto, simulado):
        e = ciclo.estado_via(conn, T0, ponto_id=p.id)
        assert e.sem_dado and not e.ocorrencia


def test_decisoes_independentes_por_ponto(conn, ponto, simulado):
    # A mesma rodada decide cada ponto pelo proprio trecho: a Varzea da Palma
    # vazia desce, a Antonio Viana movimentada fica na classe da via.
    volume(conn, em=T0, media=0, trecho=VARZEA_DA_PALMA, vigente_ate=T0 + UMA_HORA)
    volume(conn, em=T0, media=4, trecho=ANTONIO_VIANA, vigente_ate=T0 + UMA_HORA)
    for k in range(1, 13):
        agora = T0 + timedelta(seconds=5 * k)
        a = decidir(conn, ponto, agora)
        b = decidir(conn, simulado, agora)
    assert a.nivel_emitido == Decimal("1.000")
    assert b.nivel_emitido == Decimal("0.500")  # piso
