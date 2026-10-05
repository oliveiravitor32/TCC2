"""Ferramentas da sessao final de bancada, CT15 a CT20 (Quadro 17, 4.10).

Tudo pela API e pelo broker da VM, com o no real ligado a ela. O roteiro
passo a passo esta em bancada/ROTEIRO_SESSAO_CT15_CT20.md.

    python -m bancada.sessao_ct latencia            # CT15 e CT17 (30 repeticoes)
    python -m bancada.sessao_ct piso                # prepara o CT18: leva o no ao piso
    python -m bancada.sessao_ct alertas             # CT16: acompanha os alertas abertos
    python -m bancada.sessao_ct credencial          # CT19: broker sem e com credencial

A chave da API e a mesma da conferencia (bancada/chave_vm.txt ou CHAVE_API_VM).
Os resultados ficam em bancada/resultados/ct*_<data>.json.

Os criterios sao os do Quadro 17, fixados antes da sessao:
  CT15 - duty aplicado e iluminancia medida correspondentes ao nivel emitido:
         |lux / (nivel x lux da classe) - 1| <= tolerancia do diagnostico;
  CT17 - latencia inferior a 2 s em TODAS as repeticoes (RNF03).
A latencia medida vai da gravacao do evento na VM a chegada da telemetria na
VM: os dois carimbos sao do relogio do servidor (DIVERGENCIAS 25). Ela inclui
a leitura do sensor no no (duas leituras descartadas e uma valida, ate ~1,3 s
com o BH1750 em alta resolucao), e por isso e um LIMITE SUPERIOR do tempo ate
o duty aplicado, que e o que o RNF03 pede. Reporta-se tambem a latencia ate a
decisao.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bancada.calibrar import RAIZ
from bancada.destino import DestinoApi, tolerancia_do_relatorio, ultimo_relatorio

PASTA = RAIZ / "bancada" / "resultados"
LIMITE_RNF03_S = 2.0


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _gravar(nome: str, dados: dict) -> Path:
    PASTA.mkdir(parents=True, exist_ok=True)
    arq = PASTA / f"{nome}_{datetime.now():%Y%m%d_%H%M%S}.json"
    arq.write_text(json.dumps(dados, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return arq


def _ponto(api: DestinoApi, codigo: str) -> dict:
    for p in api._pedir("GET", "/pontos"):
        if p["codigo"] == codigo:
            return p
    raise SystemExit(f"ponto {codigo!r} nao cadastrado na VM")


def _publicar(api: DestinoApi, corpo: dict) -> dict:
    return api._pedir("POST", "/eventos", corpo)


# ---------------------------------------------------------------------------
# CT15 + CT17
# ---------------------------------------------------------------------------
def _esperar_decisao(api, ponto: str, evento_id: int, ate: float) -> dict | None:
    while time.monotonic() < ate:
        decs = api._pedir("GET", f"/decisoes?ponto={ponto}&limite=30")
        com = [d for d in decs if evento_id in d["evento_ids"]]
        if com:
            return min(com, key=lambda d: d["criado_em"])  # a primeira que usou o evento
        time.sleep(0.3)
    return None


def _esperar_telemetria(api, ponto: str, decisao_id: str, ate: float) -> dict | None:
    while time.monotonic() < ate:
        for t in api._pedir("GET", f"/telemetria?ponto={ponto}&limite=50"):
            if t["decisao_id"] == decisao_id:
                return t
        time.sleep(0.3)
    return None


def cmd_latencia(api: DestinoApi, args) -> int:
    p = _ponto(api, args.ponto)
    trecho, lux_classe = p["trechos"][0], float(p["lux_pleno"])
    rel = ultimo_relatorio(args.ponto)
    tol = tolerancia_do_relatorio(rel) if rel else 0.15
    print(f"{args.repeticoes} repeticoes no {args.ponto} (trecho {trecho}), intervalo {args.intervalo} s;"
          f" tolerancia do CT15 {tol:.1%}\n")

    reps = []
    for i in range(1, args.repeticoes + 1):
        agora = datetime.now(timezone.utc)
        # Ocorrencia de seguranca: decisao imediata (o evento acorda o ciclo).
        # Vigencia curta, para nao prender a luz entre as repeticoes.
        ev = _publicar(api, {
            "ocorrido_em": agora.isoformat(), "tipo": "ocorrencia", "ocorrencia": "seguranca",
            "origem": "bancada-ct17", "trecho": trecho,
            "vigente_ate": (agora + timedelta(seconds=args.intervalo)).isoformat()})
        limite = time.monotonic() + 15
        dec = _esperar_decisao(api, args.ponto, ev["id"], limite)
        tel = _esperar_telemetria(api, args.ponto, dec["id"], limite) if dec else None
        r = {"repeticao": i, "evento_id": ev["id"], "evento_recebido_em": ev["recebido_em"]}
        if dec:
            r |= {"decisao_id": dec["id"], "nivel_emitido": dec["nivel_emitido"],
                  "latencia_decisao_s": round((_iso(dec["criado_em"]) - _iso(ev["recebido_em"])).total_seconds(), 3)}
        if tel:
            esperado = dec["nivel_emitido"] * lux_classe
            razao = tel["lux_medido"] / esperado if esperado else None
            r |= {"telemetria_recebida_em": tel["recebido_em"], "duty": tel["duty"],
                  "lux_medido": tel["lux_medido"], "lux_esperado": round(esperado, 3),
                  "razao": round(razao, 4) if razao else None,
                  "ct15_ok": razao is not None and abs(razao - 1) <= tol,
                  "latencia_evento_s": round((_iso(tel["recebido_em"]) - _iso(ev["recebido_em"])).total_seconds(), 3)}
        reps.append(r)
        lat = r.get("latencia_evento_s")
        print(f"  {i:2d}: decisao {r.get('latencia_decisao_s', '-')} s | ate a telemetria "
              f"{lat if lat is not None else 'SEM TELEMETRIA'} s | lux {r.get('lux_medido', '-')}"
              f" de {r.get('lux_esperado', '-')}")
        time.sleep(max(0.0, args.intervalo - (time.monotonic() - (limite - 15))))

    lats = [r["latencia_evento_s"] for r in reps if "latencia_evento_s" in r]
    sem = sum(1 for r in reps if "latencia_evento_s" not in r)
    resumo = {
        "n": len(reps), "sem_telemetria": sem,
        "latencia_evento_s": {
            "min": min(lats, default=None), "mediana": statistics.median(lats) if lats else None,
            "p95": sorted(lats)[max(0, int(round(0.95 * len(lats))) - 1)] if lats else None,
            "max": max(lats, default=None)},
        "ct17_aprovado": sem == 0 and all(x < LIMITE_RNF03_S for x in lats),
        "ct15_aprovado": all(r.get("ct15_ok") for r in reps),
        "tolerancia_ct15": tol,
    }
    arq = _gravar("ct15_ct17_latencia", {"ponto": args.ponto, "trecho": trecho, "resumo": resumo,
                                         "repeticoes": reps})
    l = resumo["latencia_evento_s"]
    print(f"\nlatencia evento -> telemetria: min {l['min']} | mediana {l['mediana']} | "
          f"p95 {l['p95']} | max {l['max']} s; sem telemetria: {sem}")
    print(f"CT17 (todas < 2 s): {'APROVADO' if resumo['ct17_aprovado'] else 'REPROVADO'}")
    print(f"CT15 (lux corresponde ao nivel): {'APROVADO' if resumo['ct15_aprovado'] else 'REPROVADO'}")
    print(f"registro: {arq}")
    return 0 if resumo["ct17_aprovado"] and resumo["ct15_aprovado"] else 1


# ---------------------------------------------------------------------------
# CT18: leva o no ao piso
# ---------------------------------------------------------------------------
def cmd_piso(api: DestinoApi, args) -> int:
    """Publica volume zero nos trechos do ponto a cada 5 min (como a
    plataforma faria) e acompanha o nivel ate o piso. Com volume baixo e
    previsao baixa, a regra R5 leva a classe minima; a descida obedece a
    rampa (>= 5 min). Se a previsao da hora nao for baixa (R6), o nivel para
    uma classe acima: rode num horario de pouco movimento previsto."""
    p = _ponto(api, args.ponto)
    piso = float(p["piso_fracao"] or 1.0)
    print(f"publicando volume 0 nos trechos {p['trechos']} a cada 5 min; piso = {piso}")
    proxima = 0.0
    fim = time.monotonic() + args.minutos * 60
    while time.monotonic() < fim:
        if time.monotonic() >= proxima:
            agora = datetime.now(timezone.utc).isoformat()
            _publicar(api, [{"ocorrido_em": agora, "tipo": "volume", "pessoas_media": 0,
                             "periodo_s": 300, "origem": "bancada-ct18", "trecho": t}
                            for t in p["trechos"]])
            proxima = time.monotonic() + 300
        nivel = _ponto(api, args.ponto)["nivel_emitido"]
        print(f"  {datetime.now():%H:%M:%S} nivel emitido {nivel}")
        if nivel is not None and abs(nivel - piso) < 1e-3:
            print("\nNO PISO. Agora, na VM:  docker compose -f docker-compose.prod.yml stop decisao")
            print("e acompanhe o Monitor Serial: em ate 15 s deve aparecer FAILSAFE e o lux voltar a ~10.")
            print("Depois:  docker compose -f docker-compose.prod.yml start decisao")
            return 0
        time.sleep(15)
    print("nao chegou ao piso no tempo dado (veja a docstring: previsao da hora)")
    return 1


# ---------------------------------------------------------------------------
# CT16: alertas
# ---------------------------------------------------------------------------
def cmd_alertas(api: DestinoApi, args) -> int:
    print("acompanhando os alertas (Ctrl+C para parar). Desligue o 12 V e religue.")
    vistos: dict[int, dict] = {}
    try:
        while True:
            for a in api._pedir("GET", "/alertas?abertos=false&limite=20"):
                if a["ponto"] != args.ponto:
                    continue
                antes = vistos.get(a["id"])
                if antes is None or antes["encerrado_em"] != a["encerrado_em"]:
                    estado = "ENCERRADO" if a["encerrado_em"] else "ABERTO"
                    print(f"  {datetime.now():%H:%M:%S} alerta {a['id']} {a['tipo']} {estado} "
                          f"(aberto {a['aberto_em']}, encerrado {a['encerrado_em']})")
                    vistos[a["id"]] = a
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    arq = _gravar("ct16_alertas", {"ponto": args.ponto, "alertas": list(vistos.values())})
    print(f"registro: {arq}")
    return 0


# ---------------------------------------------------------------------------
# CT19: credencial no broker
# ---------------------------------------------------------------------------
def _segredos() -> dict:
    """Le URI, usuario, senha e CA do segredos.h do firmware (nada e impresso)."""
    s = (RAIZ / "firmware" / "no" / "segredos.h").read_text(encoding="utf-8")
    def define(nome):
        m = re.search(rf'#define\s+{nome}\s+"([^"]*)"', s)
        return m.group(1) if m else ""
    ca = re.search(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", s, re.S)
    uri = define("MQTT_URI")
    m = re.match(r"mqtts?://([^:/]+):(\d+)", uri)
    if not m or not ca:
        raise SystemExit("segredos.h sem MQTT_URI mqtts:// ou sem o certificado da CA")
    return {"host": m.group(1), "porta": int(m.group(2)), "usuario": define("MQTT_USUARIO"),
            "senha": define("MQTT_SENHA"), "ca": ca.group(0)}


def _tentar(seg: dict, usuario: str | None, senha: str | None) -> dict:
    import paho.mqtt.client as mqtt

    resultado: dict = {}
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ct19-{int(time.time())}")
    ctx = ssl.create_default_context(cadata=seg["ca"])
    c.tls_set_context(ctx)
    if usuario:
        c.username_pw_set(usuario, senha)

    def ao_conectar(cli, _u, _f, codigo, _p):
        resultado["codigo"] = str(codigo)
        resultado["aceito"] = not codigo.is_failure
        sock = cli.socket()
        if hasattr(sock, "version"):
            resultado["tls"] = sock.version()
            resultado["cifra"] = sock.cipher()[0] if sock.cipher() else None
        cli.disconnect()

    c.on_connect = ao_conectar
    try:
        c.connect(seg["host"], seg["porta"], keepalive=10)
        fim = time.monotonic() + 10
        while "codigo" not in resultado and time.monotonic() < fim:
            c.loop(timeout=0.5)
    except Exception as erro:  # recusa no handshake tambem e recusa
        resultado.setdefault("codigo", f"erro: {erro}")
        resultado.setdefault("aceito", False)
    resultado.setdefault("codigo", "sem resposta")
    resultado.setdefault("aceito", False)
    return resultado


def cmd_credencial(_api, args) -> int:
    seg = _segredos()
    sem = _tentar(seg, None, None)
    # Mesma credencial do no, com outro client_id: o no real continua ligado.
    com = _tentar(seg, seg["usuario"], seg["senha"])
    errada = _tentar(seg, seg["usuario"], "senha-errada-de-proposito")
    print(f"sem credencial:      {'ACEITO' if sem['aceito'] else 'RECUSADO'} ({sem['codigo']})")
    print(f"senha errada:        {'ACEITO' if errada['aceito'] else 'RECUSADO'} ({errada['codigo']})")
    print(f"com credencial:      {'ACEITO' if com['aceito'] else 'RECUSADO'} ({com['codigo']}),"
          f" {com.get('tls')} {com.get('cifra')}")
    ok = (not sem["aceito"]) and (not errada["aceito"]) and com["aceito"] and bool(com.get("tls"))
    arq = _gravar("ct19_credencial", {"host": seg["host"], "porta": seg["porta"],
                                      "sem_credencial": sem, "senha_errada": errada,
                                      "com_credencial": com, "aprovado": ok})
    print(f"CT19: {'APROVADO' if ok else 'REPROVADO'}\nregistro: {arq}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("teste", choices=["latencia", "piso", "alertas", "credencial"])
    p.add_argument("--ponto", default="BANCADA-01")
    p.add_argument("--repeticoes", type=int, default=30)
    p.add_argument("--intervalo", type=float, default=20.0, help="segundos entre repeticoes")
    p.add_argument("--minutos", type=float, default=30.0, help="piso: tempo maximo de espera")
    args = p.parse_args(argv)
    api = DestinoApi()
    acoes = {"latencia": cmd_latencia, "piso": cmd_piso, "alertas": cmd_alertas,
             "credencial": cmd_credencial}
    sys.exit(acoes[args.teste](api, args))


if __name__ == "__main__":
    main(sys.argv[1:])
