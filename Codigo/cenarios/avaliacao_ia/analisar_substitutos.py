"""Metricas do PROTOCOLO_SUBSTITUTOS.md (DIVERGENCIAS 59).

    python -m cenarios.avaliacao_ia.analisar_substitutos

Grava cenarios/resultados/avaliacao_ia_substitutos.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import psycopg

from cenarios.avaliacao_ia.analisar import AQUI, MARGEM, POTENCIA, PASSO_H, RES, _cenario, _energia, _episodios
from cenarios.executar import HORA_FIM_ATENUACAO, HORA_INICIO_ATENUACAO
from decisao import ciclo, config
from decisao.energia import trajetoria_horario_fixo
from decisao.inferencia import carregar

PREVISORES = {"xgboost": "", "media_sazonal": "_media_sazonal"}
from cenarios.avaliacao_ia.analisar import _horas
from cenarios.avaliacao_ia.gerar import NOITES


def _rels(arq: str) -> dict[str, dict]:
    d = json.loads((RES / arq).read_text(encoding="utf-8"))
    return {r["cenario"]: r for r in d["relatorios"]}


def _deficit(rels, f1, f2) -> dict:
    n = soma = 0
    for r in rels.values():
        for x in r["serie"]:
            obs = x["observada"]
            if x["ocorrencia"] or (obs is not None and obs >= f2):
                pede = 1.0
            elif obs is not None and obs >= f1:
                pede = 0.75
            else:
                continue
            if x["emitido"] < pede - MARGEM:
                n += 1
                soma += pede - x["emitido"]
    return {"min_abaixo": round(n * config.PERIODO_S / 60, 1),
            "deficit_medio_fracao": round(soma / n, 3) if n else 0.0}


def melbourne(piso, f1, f2) -> dict:
    from cenarios.avaliacao_ia.analisar import melbourne as m57  # noqa: F401 (mesmas definicoes)
    reat = _rels(f"avaliacao_ia_{NOITES}_reativo.json")
    metr = json.loads((RES / "avaliacao_ia_metricas.json").read_text(encoding="utf-8"))
    depois = metr["melbourne"]["hora_apos_a_noite"]
    saida = {}
    for prev, suf in PREVISORES.items():
        rels = _rels(f"avaliacao_ia_{NOITES}_antecipado{suf}.json")
        nomes = sorted(rels)
        e = [_energia(rels[n]) for n in nomes]
        jan = sum(rels[n]["h3"]["ciclos_em_janela_baixa"] for n in nomes)
        tr = sum(rels[n]["h3"]["ciclos_em_transicao"] for n in nomes)
        atrasos = []
        seg = seg_ok = 0
        for n in nomes:
            s = rels[n]["serie"]
            for i, j in _episodios(s, f1):
                chegou = next((k for k in range(i, j) if s[k]["emitido"] <= piso + MARGEM), j)
                atrasos.append((chegou - i) * config.PERIODO_S / 60)
            horas = _horas(_cenario(NOITES, n))
            if depois.get(n) is not None:
                horas.append(depois[n])
            for xa, xr in zip(s, reat[n]["serie"]):
                h = int(xa["minuto"] // 60) + 1
                if h >= len(horas) or xa["observada"] is None:
                    continue
                if xa["emitido"] > xr["emitido"] + 0.005:
                    seg += 1
                    seg_ok += horas[h] >= f1
        saida[prev] = {
            "violacoes": {k: sum(rels[n]["violacoes"][k] for n in nomes) for k in ("piso", "taxa")},
            "energia_x_pleno": round(sum(x[0] for x in e) / sum(x[1] for x in e), 4),
            "energia_x_fixo": round(sum(x[0] for x in e) / sum(x[2] for x in e), 4),
            "h3_primaria": round(tr / jan, 4) if jan else None,
            "h3_secundaria_min": round(sum(atrasos) / len(atrasos), 1) if atrasos else None,
            "ciclos_contidos": seg,
            "acerto_da_contencao": round(seg_ok / seg, 4) if seg else None,
            "deficit": _deficit(rels, f1, f2),
        }
    saida["referencia_segurar_sempre"] = metr["melbourne"]["contencao"]["mamdani"]["referencia_segurar_sempre"]
    return saida


def camera(piso) -> dict:
    saida = {}
    for prev, suf in PREVISORES.items():
        rels = _rels(f"avaliacao_ia_camera_antecipado{suf}.json")
        for rotulo in ("inicio_da_noite", "madrugada"):
            c, f = rels[f"camera_{rotulo}_controle"]["serie"], rels[f"camera_{rotulo}_falha"]["serie"]
            de, ate = _cenario("camera", f"camera_{rotulo}_falha")["falha_min"]
            jan = [(xc, xf) for xc, xf in zip(c, f) if de <= xc["minuto"] < ate]
            saida.setdefault(rotulo, {})[prev] = {
                "luz_perdida_media": round(sum(xc["emitido"] - xf["emitido"] for xc, xf in jan) / len(jan), 4),
                "energia_falha_wh": round(sum(xf["emitido"] for _, xf in jan) * POTENCIA * PASSO_H, 3),
            }
    return saida


def ruido() -> dict:
    saida = {}
    for modo, arq in (("mamdani", "avaliacao_ia_ruido_antecipado.json"),
                      ("tabela", "avaliacao_ia_ruido_antecipado_degraus.json")):
        rels = _rels(arq)
        nomes = sorted(rels)
        e = [_energia(rels[n]) for n in nomes]
        mud = [rels[n]["mudancas"] for n in nomes]
        saida[modo] = {
            "violacoes": {k: sum(rels[n]["violacoes"][k] for n in nomes) for k in ("piso", "taxa")},
            "energia_x_pleno": round(sum(x[0] for x in e) / sum(x[1] for x in e), 4),
            "variacao_total": round(sum(m["variacao_total"] for m in mud), 3),
            "inversoes": sum(m["inversoes_de_sentido"] for m in mud),
            "subidas_bruscas": sum(m["subidas_bruscas"] for m in mud),
            "por_cenario": {n: {"variacao_total": rels[n]["mudancas"]["variacao_total"],
                                "inversoes": rels[n]["mudancas"]["inversoes_de_sentido"],
                                "subidas_bruscas": rels[n]["mudancas"]["subidas_bruscas"]}
                            for n in nomes},
        }
    return saida


def main() -> None:
    base = carregar(config.REGRAS)
    f1 = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
    f2 = (base.mov["alta"][0] + base.mov["alta"][1]) / 2
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        piso = float(ciclo.criterio(conn, "P3").piso)
    m = {"teste1_melbourne": melbourne(piso, f1, f2), "teste1_camera": camera(piso), "teste2_ruido": ruido()}
    (RES / "avaliacao_ia_substitutos.json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(m, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
