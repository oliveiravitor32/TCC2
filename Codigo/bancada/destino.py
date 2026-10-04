"""Para onde vao os resultados da bancada (conferencia e calibracao).

Tres destinos com a mesma interface:
  - DestinoBanco: o Postgres local (docker compose), como sempre;
  - DestinoApi: a API da VM (POST /bancada/...), quando o no esta ligado a
    VM e a sessao precisa ficar no banco que recebe a telemetria. Exige a
    CHAVE_API (a secreta, nunca a do painel) na variavel CHAVE_API_VM;
  - SemDestino: sem banco, so arquivo (a conferencia roda igual).

A tolerancia da conferencia vem do banco local, quando ha, ou do JSON da
ultima calibracao real (bancada/resultados/sessao_*.json), com a mesma regra
de decisao.diagnostico.tolerancia_do_ponto.
"""

from __future__ import annotations

import json
import os
import statistics
import urllib.error
import urllib.request

import psycopg

from decisao import config
from decisao.diagnostico import tolerancia_do_ponto
from decisao.sessao_bancada import registrar_calibracao, registrar_conferencia

API_VM_PADRAO = "https://tcc-iluminacao-publica.duckdns.org"


def _pasta():
    from bancada.calibrar import RAIZ

    return RAIZ / "bancada" / "resultados"


# ---------------------------------------------------------------------------
# Tolerancia a partir do JSON da ultima calibracao
# ---------------------------------------------------------------------------
def tolerancia_do_relatorio(rel: dict) -> float:
    """Mesma regra de diagnostico.tolerancia_do_ponto, a partir do JSON da
    ultima calibracao (para quando o banco local nao e o destino)."""
    lux_piso = float(rel["lux_piso"])
    por_duty: dict[int, list[float]] = {}
    for pontos in rel.get("series", {}).values():
        for d, lux in pontos:
            por_duty.setdefault(int(d), []).append(float(lux))
    por_duty.setdefault(int(rel["duty_pleno"]), []).extend(rel.get("repeticoes_pleno_lux", []))
    por_duty.setdefault(int(rel["duty_piso"]), []).extend(rel.get("repeticoes_piso_lux", []))
    dispersoes = [
        statistics.stdev(v) / statistics.fmean(v)
        for v in por_duty.values()
        if len(v) > 1 and statistics.fmean(v) >= lux_piso * 0.98
    ]
    pela_dispersao = config.K_SIGMA * max(dispersoes, default=0.0)
    pela_resolucao = config.DEGRAUS_TOLERANCIA * config.RESOLUCAO_SENSOR_LUX / lux_piso
    return max(pela_dispersao, pela_resolucao)


def ultimo_relatorio(ponto: str) -> dict | None:
    relatorios = []
    for arq in _pasta().glob("sessao_*.json"):
        if "SIMULADA" in arq.name:
            continue
        rel = json.loads(arq.read_text(encoding="utf-8"))
        if rel.get("ponto") == ponto and not rel.get("simulada"):
            relatorios.append(rel)
    return max(relatorios, key=lambda r: r["gerado_em"], default=None)


def _tolerancia_do_arquivo(ponto: str) -> tuple[float, str]:
    rel = ultimo_relatorio(ponto)
    if rel is None:
        raise SystemExit("sem bancada/resultados/sessao_*.json: nao ha contra o que conferir")
    return tolerancia_do_relatorio(rel), f"arquivo da sessao {rel['sessao_id']}"


# ---------------------------------------------------------------------------
# Destinos
# ---------------------------------------------------------------------------
class SemDestino:
    """Sem banco: classe e tolerancia do JSON; nada e gravado fora do arquivo."""

    nome = "so arquivo"
    grava = False

    def classe(self, ponto: str) -> tuple[str, float, float]:
        rel = ultimo_relatorio(ponto)
        if rel is None:
            raise SystemExit("sem banco e sem bancada/resultados/sessao_*.json")
        return rel["classe"], float(rel["lux_classe"]), float(rel["lux_piso"])

    def tolerancia(self, ponto: str) -> tuple[float, str]:
        return _tolerancia_do_arquivo(ponto)

    def conferencia(self, ponto, lux_residual, aprovada, observacao) -> int | None:
        return None

    def calibracao(self, ponto, lux_residual, linhas, observacao, potencia_plena_w=None) -> int:
        raise SystemExit("recalibrar exige o banco local (docker compose up -d) ou --vm")

    def fechar(self) -> None:
        pass


class DestinoBanco:
    """Postgres local. Simulada: tudo e desfeito ao fechar."""

    grava = True

    def __init__(self, conn: psycopg.Connection, simulada: bool = False) -> None:
        self.conn, self.simulada = conn, simulada
        self.nome = "banco local"

    def classe(self, ponto: str) -> tuple[str, float, float]:
        from bancada.calibrar import classe_do_ponto

        _pid, classe, lux, lux_piso = classe_do_ponto(self.conn, ponto)
        return classe, lux, lux_piso

    def tolerancia(self, ponto: str) -> tuple[float, str]:
        from bancada.calibrar import classe_do_ponto

        pid = classe_do_ponto(self.conn, ponto)[0]
        return tolerancia_do_ponto(self.conn, pid), "banco: ultima calibracao"

    def conferencia(self, ponto, lux_residual, aprovada, observacao) -> int:
        return registrar_conferencia(self.conn, ponto, lux_residual, aprovada, observacao)[0]

    def calibracao(self, ponto, lux_residual, linhas, observacao, potencia_plena_w=None) -> int:
        return registrar_calibracao(self.conn, ponto, lux_residual, linhas, observacao,
                                    potencia_plena_w)

    def fechar(self) -> None:
        if self.simulada:
            self.conn.rollback()  # numero sintetico nunca fica no banco
        self.conn.close()


class DestinoApi:
    """API da VM: a sessao fica no banco que recebe a telemetria do no."""

    grava = True

    def __init__(self) -> None:
        self.url = os.environ.get("API_URL_VM", API_VM_PADRAO).rstrip("/")
        # A chave vem do ambiente, e nao da linha de comando, para nao ficar
        # no historico do terminal. E a CHAVE_API do .env da VM.
        self.chave = os.environ.get("CHAVE_API_VM", "")
        if not self.chave:
            raise SystemExit(
                "defina CHAVE_API_VM com a CHAVE_API do .env da VM (a secreta, nao a do painel);\n"
                "  veja deploy/ROTEIRO.md, secao 10"
            )
        self.nome = f"VM ({self.url})"

    def _pedir(self, metodo: str, caminho: str, corpo: dict | None = None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(
            self.url + caminho, data=dados, method=metodo,
            headers={"Content-Type": "application/json", "X-Chave-Api": self.chave},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as erro:
            if erro.code == 401:
                raise SystemExit("a VM recusou a chave: CHAVE_API_VM deve ser a CHAVE_API do .env "
                                 "da VM (a do painel nao serve aqui)") from None
            raise SystemExit(f"a VM respondeu {erro.code}: {erro.read().decode(errors='replace')}") from None
        except urllib.error.URLError as erro:
            raise SystemExit(f"nao consegui falar com a VM em {self.url}: {erro.reason}") from None

    def classe(self, ponto: str) -> tuple[str, float, float]:
        for p in self._pedir("GET", "/pontos"):
            if p["codigo"] == ponto:
                lux = float(p["lux_pleno"])
                return p["classe_codigo"], lux, lux * float(p["piso_fracao"] or 1.0)
        raise SystemExit(f"ponto {ponto!r} nao cadastrado na VM")

    def tolerancia(self, ponto: str) -> tuple[float, str]:
        return _tolerancia_do_arquivo(ponto)

    def conferencia(self, ponto, lux_residual, aprovada, observacao) -> int:
        r = self._pedir("POST", "/bancada/sessoes", {
            "ponto": ponto, "lux_residual": round(lux_residual, 3),
            "aprovada": aprovada, "observacao": observacao[:500]})
        return r["sessao_id"]

    def calibracao(self, ponto, lux_residual, linhas, observacao, potencia_plena_w=None) -> int:
        r = self._pedir("POST", "/bancada/calibracoes", {
            "ponto": ponto, "lux_residual": round(lux_residual, 3), "observacao": observacao[:500],
            "potencia_plena_w": potencia_plena_w,
            "linhas": [{"serie": s, "duty": round(d, 6), "lux_medido": round(l, 3)}
                       for s, d, l in linhas]})
        return r["sessao_id"]

    def fechar(self) -> None:
        pass


def abrir(vm: bool, simulada: bool, obrigatorio: bool) -> SemDestino | DestinoBanco | DestinoApi:
    """--vm: API da VM. Sem --vm: banco local; se ele estiver parado, so
    arquivo (ou erro, quando o banco e obrigatorio, como na calibracao)."""
    if vm:
        if simulada:
            raise SystemExit("--simulada com --vm gravaria numero sintetico na VM: nao permitido")
        return DestinoApi()
    try:
        conn = psycopg.connect(config.DATABASE_URL, autocommit=not simulada, connect_timeout=5)
    except psycopg.OperationalError as erro:
        if obrigatorio:
            raise SystemExit(f"nao consegui falar com o Postgres: {erro}\n"
                             "  Abra o Docker Desktop e rode:  docker compose up -d") from None
        print("AVISO: banco local indisponivel (Docker parado?). A conferencia roda igual;\n"
              "       o resultado fica so no arquivo, e recalibrar exige o banco ou --vm.")
        return SemDestino()
    return DestinoBanco(conn, simulada)
