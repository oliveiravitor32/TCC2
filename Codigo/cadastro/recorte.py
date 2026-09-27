"""Baixa um recorte real do GeoSampa e gera a carga do cadastro espacial.

    python -m cadastro.recorte baixar     # WFS publico -> cadastro/dados/*.json
    python -m cadastro.recorte sql        # recorte -> db/seed_cadastro.sql

O recorte fica versionado (com data de extracao e consulta usada) para que a
carga seja reproduzivel sem rede. Area: quarteiroes do Jardim Helena, zona
leste, ruas locais residenciais (cenario de classe P3, 3.8).

Os pontos de luz controlados pelo sistema sao os que tem no: cada um
"representa" um poste real do recorte (PONTOS abaixo). Os demais postes do
recorte ficam no arquivo, mas nao viram ponto_de_luz: o servico so decide
para luminarias que comanda.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from .associar import CRITERIO, associar, postes_do_geojson, trechos_do_geojson

WFS = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs"
BBOX = (354520, 7401880, 354730, 7402090)  # EPSG:31983, cerca de 210 m x 210 m
CAMADAS = {"trechos": "geoportal:segmento_logradouro", "postes": "geoportal:iluminacao_publica"}

DADOS = Path(__file__).parent / "dados"
RECORTE = DADOS / "recorte_jardim_helena.json"
SEED = Path(__file__).resolve().parent.parent / "db" / "seed_cadastro.sql"

# codigo do ponto no sistema (= usuario MQTT e topico) -> placa do poste real
PONTOS = {
    "BANCADA-01": "IP0412418",   # R. Antonio Viana, perto da esquina com a R. Ascenso Fernandes
    "SIMULADO-02": "IP0412401",  # R. Varzea da Palma, meio de quadra
}


def _url(camada: str) -> str:
    q = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": camada, "outputFormat": "application/json", "srsName": "EPSG:31983",
        "bbox": ",".join(map(str, BBOX)) + ",urn:ogc:def:crs:EPSG::31983",
    }
    return WFS + "?" + urllib.parse.urlencode(q)


def baixar() -> None:
    DADOS.mkdir(exist_ok=True)
    saida = {"fonte": "GeoSampa (Prefeitura de Sao Paulo), servico WFS publico",
             "extraido_em": date.today().isoformat(), "crs": "EPSG:31983", "bbox": BBOX}
    for chave, camada in CAMADAS.items():
        url = _url(camada)
        with urllib.request.urlopen(url, timeout=120) as r:
            fc = json.load(r)
        saida[chave] = {"camada": camada, "consulta": url, "total": len(fc["features"]), "geojson": fc}
        print(f"{camada}: {len(fc['features'])} feicoes")
    RECORTE.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado: {RECORTE}")


def _txt(v) -> str:
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def gerar_sql() -> str:
    rec = json.loads(RECORTE.read_text(encoding="utf-8"))
    trechos = trechos_do_geojson(rec["trechos"]["geojson"])
    postes = {p.placa: p for p in postes_do_geojson(rec["postes"]["geojson"])}
    faltando = [pl for pl in PONTOS.values() if pl not in postes]
    if faltando:
        raise SystemExit(f"placas fora do recorte: {faltando}")

    linhas = [
        "-- Cadastro espacial (DIVERGENCIAS 54). GERADO por `python -m cadastro.recorte sql`;",
        "-- nao editar a mao. Fonte: " + rec["fonte"] + f", extraido em {rec['extraido_em']}.",
        "-- Trechos = segmentos de logradouro; pontos = postes reais (placa), EPSG:31983.",
        "",
        "INSERT INTO trecho_via (id, codlog, tipo_logradouro, nome_logradouro,",
        "                        numero_inicial, numero_final, geometria, fonte, extraido_em) VALUES",
    ]
    valores = []
    for t in sorted(trechos, key=lambda t: t.id):
        geo = json.dumps({"type": "LineString", "coordinates": [[round(x, 2), round(y, 2)] for x, y in t.linha]})
        valores.append(
            f"  ({t.id}, {_txt(t.codlog)}, {_txt(t.tipo)}, {_txt(t.nome)}, "
            f"{t.numero_inicial if t.numero_inicial is not None else 'NULL'}, "
            f"{t.numero_final if t.numero_final is not None else 'NULL'}, "
            f"{_txt(geo)}::jsonb, 'GeoSampa segmento_logradouro', '{rec['extraido_em']}')"
        )
    linhas.append(",\n".join(valores))
    linhas.append("ON CONFLICT (id) DO NOTHING;\n")

    linhas.append("-- Pontos com no: codigo do sistema -> poste real do recorte.")
    for codigo, placa in PONTOS.items():
        p = postes[placa]
        linhas.append(
            "INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n)\n"
            f"VALUES ({_txt(codigo)}, {_txt(p.endereco)}, 'P3', {_txt(placa)}, {p.x:.2f}, {p.y:.2f})\n"
            "ON CONFLICT (codigo) DO UPDATE SET placa = EXCLUDED.placa, logradouro = EXCLUDED.logradouro,\n"
            "    utm_e = EXCLUDED.utm_e, utm_n = EXCLUDED.utm_n;"
        )
    linhas.append("")

    linhas.append(f"-- Associacao trecho x ponto: {CRITERIO}.")
    pares = associar([postes[pl] for pl in PONTOS.values()], trechos)
    for a in pares:
        codigo = next(c for c, pl in PONTOS.items() if pl == a.placa)
        linhas.append(
            "INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)\n"
            f"SELECT {a.trecho_id}, id, {a.distancia_m}, {_txt(CRITERIO)} FROM ponto_de_luz WHERE codigo = {_txt(codigo)}\n"
            "ON CONFLICT DO NOTHING;"
        )
    return "\n".join(linhas) + "\n"


def main() -> None:
    acao = sys.argv[1] if len(sys.argv) > 1 else ""
    if acao == "baixar":
        baixar()
    elif acao == "sql":
        SEED.write_text(gerar_sql(), encoding="utf-8")
        print(f"gravado: {SEED}")
    else:
        raise SystemExit("uso: python -m cadastro.recorte baixar|sql")


if __name__ == "__main__":
    main()
