"""Associacao espacial trecho x ponto (DIVERGENCIAS 54): geometria e o
recorte real do GeoSampa versionado em cadastro/dados."""

import json

import pytest

from cadastro.associar import (RAIO_M, Poste, Trecho, associar, distancia_linha,
                               distancia_segmento, postes_do_geojson, trechos_do_geojson)
from cadastro.recorte import PONTOS, RECORTE, SEED, gerar_sql


def test_distancia_ao_segmento():
    assert distancia_segmento((5, 3), (0, 0), (10, 0)) == 3        # projecao dentro
    assert distancia_segmento((13, 4), (0, 0), (10, 0)) == 5       # alem da ponta
    assert distancia_segmento((1, 1), (0, 0), (0, 0)) == pytest.approx(2 ** 0.5)


def test_distancia_a_linha_poligonal():
    assert distancia_linha((12, 5), [(0, 0), (10, 0), (10, 10)]) == 2


def test_esquina_fica_nos_dois_trechos():
    a = Trecho(1, None, "R", "A", None, None, ((0, 0), (100, 0)))
    b = Trecho(2, None, "R", "B", None, None, ((0, 0), (0, 100)))
    esquina = Poste("P1", None, 5, 5)
    meio = Poste("P2", None, 50, 4)
    pares = {(x.placa, x.trecho_id) for x in associar([esquina, meio], [a, b])}
    assert pares == {("P1", 1), ("P1", 2), ("P2", 1)}


def test_raio_e_inclusivo_e_nada_alem_dele():
    t = Trecho(1, None, None, "X", None, None, ((0, 0), (100, 0)))
    assert associar([Poste("P", None, 50, RAIO_M)], [t])
    assert not associar([Poste("P", None, 50, RAIO_M + 0.01)], [t])


@pytest.fixture(scope="module")
def recorte():
    return json.loads(RECORTE.read_text(encoding="utf-8"))


def test_recorte_real_tem_origem_e_data(recorte):
    assert recorte["crs"] == "EPSG:31983" and recorte["extraido_em"]
    assert "segmento_logradouro" in recorte["trechos"]["consulta"]


def test_placas_repetidas_no_cadastro_entram_uma_vez(recorte):
    postes = postes_do_geojson(recorte["postes"]["geojson"])
    assert len({p.placa for p in postes}) == len(postes)


def test_pontos_do_sistema_estao_no_recorte_e_tem_trecho(recorte):
    trechos = trechos_do_geojson(recorte["trechos"]["geojson"])
    postes = {p.placa: p for p in postes_do_geojson(recorte["postes"]["geojson"])}
    for placa in PONTOS.values():
        assert associar([postes[placa]], trechos), placa


def test_seed_gerado_esta_em_dia_com_o_recorte():
    # Quem mexer no recorte ou na regra tem de regerar o seed.
    assert SEED.read_text(encoding="utf-8") == gerar_sql()
