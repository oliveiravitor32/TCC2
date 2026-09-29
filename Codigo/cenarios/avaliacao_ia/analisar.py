"""Metricas do PROTOCOLO.md sobre os relatorios da avaliacao das IAs.

    python -m cenarios.avaliacao_ia.analisar

Le cenarios/resultados/avaliacao_ia_*.json (gerados com --serie) e grava
cenarios/resultados/avaliacao_ia_metricas.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import psycopg

from decisao import ciclo, config
from decisao.inferencia import carregar

AQUI = Path(__file__).resolve().parent
RES = AQUI.parent / "resultados"
PASSO_H = config.PERIODO_S / 3600
POTENCIA = 40.0  # REF-40W, Quadro 9
MARGEM = 0.02


def _rel(pasta: str, modo: str) -> dict[str, dict]:
    d = json.loads((RES / f"avaliacao_ia_{pasta}_{modo}.json").read_text(encoding="utf-8"))
    return {r["cenario"]: r for r in d["relatorios"]}


def _cenario(pasta: str, nome: str) -> dict:
    return json.loads((AQUI / pasta / f"{nome}.json").read_text(encoding="utf-8"))


def _energia(r) -> tuple[float, float, float]:
    e = r["energia"]["REF-40W"]
    return e["adaptativo_wh"], e["pleno_constante_wh"], e["horario_fixo_wh"]


def _episodios(serie, f1) -> list[tuple[int, int]]:
    """Faixas [i, j) de ciclos consecutivos com volume observado baixo, >= 30 min."""
    minimo = int(30 * 60 / config.PERIODO_S)
    eps, i = [], None
    for k, x in enumerate(serie + [{"observada": None}]):
        baixo = x["observada"] is not None and x["observada"] < f1
        if baixo and i is None:
            i = k
        elif not baixo and i is not None:
            if k - i >= minimo:
                eps.append((i, k))
            i = None
    return eps


def melbourne(piso: float, f1: float) -> dict:
    modos = {m: _rel("melbourne", m) for m in
             ("antecipado", "reativo", "antecipado_degraus", "reativo_degraus")}
    nomes = sorted(modos["antecipado"])
    saida = {"por_modo": {}, "por_noite": {}, "contencao": {}}

    for modo, rels in modos.items():
        e = [_energia(rels[n]) for n in nomes]
        jan = sum(rels[n]["h3"]["ciclos_em_janela_baixa"] for n in nomes)
        tr = sum(rels[n]["h3"]["ciclos_em_transicao"] for n in nomes)
        atrasos = []
        for n in nomes:
            s = rels[n]["serie"]
            for i, j in _episodios(s, f1):
                chegou = next((k for k in range(i, j) if s[k]["emitido"] <= piso + MARGEM), j)
                atrasos.append((chegou - i) * config.PERIODO_S / 60)
        mud = [rels[n]["mudancas"] for n in nomes]
        saida["por_modo"][modo] = {
            "violacoes": {k: sum(rels[n]["violacoes"][k] for n in nomes) for k in ("piso", "taxa")},
            "energia_x_pleno": sum(x[0] for x in e) / sum(x[1] for x in e),
            "energia_x_fixo": sum(x[0] for x in e) / sum(x[2] for x in e),
            "h3_primaria": tr / jan if jan else None,
            "h3_secundaria_min": sum(atrasos) / len(atrasos) if atrasos else None,
            "episodios": len(atrasos),
            "variacao_total": round(sum(m["variacao_total"] for m in mud), 3),
            "inversoes": sum(m["inversoes_de_sentido"] for m in mud),
            "subidas_bruscas": sum(m["subidas_bruscas"] for m in mud),
        }
        for n in nomes:
            saida["por_noite"].setdefault(n, {})[modo] = {
                "energia_x_pleno": round(_energia(rels[n])[0] / _energia(rels[n])[1], 4),
                "h3": rels[n]["h3"]["fracao_em_transicao"],
                "variacao_total": rels[n]["mudancas"]["variacao_total"],
                "inversoes": rels[n]["mudancas"]["inversoes_de_sentido"],
            }

    # Metrica 5: quando a previsao segura a luz, o movimento veio? O volume
    # real da hora seguinte a ultima hora da noite (06h-07h) nao esta no
    # cenario: vem da mesma serie real, com a mesma normalizacao (gerar.py).
    from cenarios.avaliacao_ia.gerar import NOITE_H, _serie
    import pandas as pd
    serie_real, _ = _serie()
    sorteio = json.loads((AQUI / "sorteio.json").read_text(encoding="utf-8"))
    depois = {}
    for x in sorteio["melbourne"]:
        ts = pd.Timestamp(x["inicio"]) + pd.Timedelta(hours=NOITE_H)
        v = serie_real[(serie_real.location_id == x["sensor"]) & (serie_real.ts == ts)].nivel
        depois[x["cenario"]] = float(v.iloc[0]) if len(v) else None
    saida["hora_apos_a_noite"] = depois
    for par, (ant, rea) in {"mamdani": ("antecipado", "reativo"),
                            "degraus": ("antecipado_degraus", "reativo_degraus")}.items():
        seg = seg_ok = baixo = baixo_ok = 0
        for n in nomes:
            horas = [ev["nivel"] for ev in _cenario("melbourne", n)["eventos"][::12]]
            if depois[n] is not None:
                horas.append(depois[n])
            sa, sr = modos[ant][n]["serie"], modos[rea][n]["serie"]
            for xa, xr in zip(sa, sr):
                h = int(xa["minuto"] // 60) + 1
                if h >= len(horas) or xa["observada"] is None:
                    continue
                veio = horas[h] >= f1
                if xa["observada"] < f1:
                    baixo += 1
                    baixo_ok += veio
                if xa["emitido"] > xr["emitido"] + 0.005:
                    seg += 1
                    seg_ok += veio
        saida["contencao"][par] = {
            "ciclos_contidos": seg,
            "acerto_da_contencao": seg_ok / seg if seg else None,
            "referencia_segurar_sempre": baixo_ok / baixo if baixo else None,
        }
    return saida


def camera(piso: float) -> dict:
    saida = {}
    for modo in ("antecipado", "reativo"):
        rels = _rel("camera", modo)
        for rotulo in ("inicio_da_noite", "madrugada"):
            c, f = rels[f"camera_{rotulo}_controle"]["serie"], rels[f"camera_{rotulo}_falha"]["serie"]
            de, ate = _cenario("camera", f"camera_{rotulo}_falha")["falha_min"]
            jan = [(xc, xf) for xc, xf in zip(c, f) if de <= xc["minuto"] < ate]
            perdida = sum(xc["emitido"] - xf["emitido"] for xc, xf in jan) / len(jan)
            no_minimo = sum(1 for xc, xf in jan
                            if xf["emitido"] <= piso + MARGEM and xc["emitido"] > piso + MARGEM)
            saida.setdefault(rotulo, {})[modo] = {
                "luz_perdida_media": round(perdida, 4),
                "min_na_minima_indevidamente": round(no_minimo * config.PERIODO_S / 60, 1),
                "energia_falha_wh": round(sum(xf["emitido"] for _, xf in jan) * POTENCIA * PASSO_H, 3),
                "energia_controle_wh": round(sum(xc["emitido"] for xc, _ in jan) * POTENCIA * PASSO_H, 3),
            }
    for rotulo in saida:
        a, r = saida[rotulo]["antecipado"], saida[rotulo]["reativo"]
        saida[rotulo]["custo_da_protecao_wh"] = round(a["energia_falha_wh"] - r["energia_falha_wh"], 3)
    return saida


def main() -> None:
    base = carregar(config.REGRAS)
    f1 = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        piso = float(ciclo.criterio(conn, "P3").piso)
    m = {"melbourne": melbourne(piso, f1), "camera": camera(piso)}
    (RES / "avaliacao_ia_metricas.json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"melbourne": {k: m["melbourne"][k] for k in ("por_modo", "contencao")},
                      "camera": m["camera"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
