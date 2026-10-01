"""Metricas do PROTOCOLO_SUAVIDADE.md (DIVERGENCIAS 61).

    python -m cenarios.avaliacao_ia.analisar_suavidade

Grava cenarios/resultados/avaliacao_ia_suavidade.json.
"""

from __future__ import annotations

import json

import psycopg

from cenarios.avaliacao_ia.analisar import MARGEM, RES, _cenario, _energia, _episodios
from decisao import ciclo, config
from decisao.inferencia import carregar

MODOS = {"mamdani": "avaliacao_ia_suavidade_antecipado.json",
         "tabela": "avaliacao_ia_suavidade_antecipado_degraus.json",
         "tabela_histerese": "avaliacao_ia_suavidade_antecipado_degraus_histerese.json"}
LIMIARES = {"15": 0.15, "6": 0.06}
DEFICIT_2LUX = 0.2


def main() -> None:
    base = carregar(config.REGRAS)
    f1 = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
    f2 = (base.mov["alta"][0] + base.mov["alta"][1]) / 2
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        piso = float(ciclo.criterio(conn, "P3").piso)
    passo_min = config.PERIODO_S / 60
    saida = {}
    for modo, arq in MODOS.items():
        d = json.loads((RES / arq).read_text(encoding="utf-8"))
        tot = {f"perceptiveis_{k}": 0 for k in LIMIARES}
        tot.update({"subidas_perceptiveis_15": 0, "min_2lux_abaixo": 0.0, "variacao_total": 0.0, "inversoes": 0})
        energia, atrasos, viol, por = [], [], {"piso": 0, "taxa": 0}, {}
        for r in d["relatorios"]:
            s = r["serie"]
            niveis = [x["emitido"] for x in s]
            rel = [(b - a) / a for a, b in zip(niveis, niveis[1:])]
            c = {f"perceptiveis_{k}": sum(1 for v in rel if abs(v) >= lim - 1e-9) for k, lim in LIMIARES.items()}
            c["subidas_perceptiveis_15"] = sum(1 for v in rel if v >= 0.15 - 1e-9)
            # Pedido sobre o volume PUBLICADO no cenario, igual para os tres modos.
            publicado = {e["em_min"]: e["nivel"] for e in _cenario("suavidade", r["cenario"])["eventos"]}
            abaixo = 0
            for x in s:
                v = publicado[int(x["minuto"] // 5) * 5]
                pede = 1.0 if v >= f2 else 0.75 if v >= f1 else None
                if pede is not None and x["emitido"] <= pede - DEFICIT_2LUX + 1e-9:
                    abaixo += 1
            c["min_2lux_abaixo"] = round(abaixo * passo_min, 1)
            for i, j in _episodios(s, f1):
                chegou = next((k for k in range(i, j) if s[k]["emitido"] <= piso + MARGEM), j)
                atrasos.append((chegou - i) * passo_min)
            c["variacao_total"] = r["mudancas"]["variacao_total"]
            c["inversoes"] = r["mudancas"]["inversoes_de_sentido"]
            e = _energia(r)
            c["energia_x_pleno"] = round(e[0] / e[1], 4)
            energia.append(e)
            for k in viol:
                viol[k] += r["violacoes"][k]
            for k in tot:
                tot[k] += c[k]
            por[r["cenario"]] = c
        tot["variacao_total"] = round(tot["variacao_total"], 3)
        tot["min_2lux_abaixo"] = round(tot["min_2lux_abaixo"], 1)
        saida[modo] = {**tot, "violacoes": viol,
                       "energia_x_pleno": round(sum(x[0] for x in energia) / sum(x[1] for x in energia), 4),
                       "atraso_ate_minima_min": round(sum(atrasos) / len(atrasos), 1) if atrasos else None,
                       "episodios": len(atrasos), "por_cenario": por}
    (RES / "avaliacao_ia_suavidade.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False) + "\n",
                                                     encoding="utf-8")
    print(json.dumps({m: {k: v for k, v in x.items() if k != "por_cenario"} for m, x in saida.items()},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
