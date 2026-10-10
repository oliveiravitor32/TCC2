"""Teste curto do estado do no antes do comando (DIVERGENCIAS 74, 3.12.9).

    python -m bancada.teste_estado_antes

Desce o ponto (volume 0 nos trechos), espera a rampa, sobe por ocorrencia de
seguranca e confere nivel_antes/lux_antes na telemetria da subida; no fim,
encerra a ocorrencia. A chave vem de bancada/chave_vm.txt e nao e impressa.
Resultado de 10/10/2026: bancada/resultados/estado_antes_20261010.json.
"""
import time
from datetime import datetime, timedelta, timezone

from bancada.destino import DestinoApi

P = "BANCADA-01"
ORIGEM = "bancada-item74"
ESPERA_RAMPA_S = 340


def agora():
    return datetime.now(timezone.utc)


def log(*a):
    print(f"{datetime.now():%H:%M:%S}", *a, flush=True)


def main() -> None:
    api = DestinoApi()
    ponto = [p for p in api._pedir("GET", "/pontos") if p["codigo"] == P][0]
    trechos = ponto["trechos"]
    log("trechos", trechos)

    for t in trechos:
        api._pedir("POST", "/eventos", {"ocorrido_em": agora().isoformat(), "tipo": "volume",
                                        "pessoas_media": 0, "periodo_s": 300, "trecho": t, "origem": ORIGEM})
    log("volume 0 publicado")
    time.sleep(20)
    d = api._pedir("GET", f"/decisoes?ponto={P}&limite=1")[0]
    log("decisao", d["id"][:8], "emitido", d["nivel_emitido"])

    log(f"esperando a rampa ({ESPERA_RAMPA_S} s)")
    time.sleep(ESPERA_RAMPA_S)

    api._pedir("POST", "/eventos", {"ocorrido_em": agora().isoformat(), "tipo": "ocorrencia",
                                    "ocorrencia": "seguranca", "trecho": trechos[0], "origem": ORIGEM,
                                    "vigente_ate": (agora() + timedelta(minutes=5)).isoformat()})
    log("ocorrencia publicada")
    fim = time.monotonic() + 60
    tel = None
    while time.monotonic() < fim:
        d = api._pedir("GET", f"/decisoes?ponto={P}&limite=1")[0]
        ts = [t for t in api._pedir("GET", f"/telemetria?ponto={P}&limite=5") if t["decisao_id"] == d["id"]]
        if ts and d["nivel_emitido"] >= 0.99:
            tel = ts[0]
            break
        time.sleep(2)
    log("telemetria da subida:", tel)

    api._pedir("POST", "/eventos", {"ocorrido_em": agora().isoformat(), "tipo": "ocorrencia",
                                    "ocorrencia": "encerrada", "trecho": trechos[0], "origem": ORIGEM})
    log("ocorrencia encerrada")


if __name__ == "__main__":
    main()
