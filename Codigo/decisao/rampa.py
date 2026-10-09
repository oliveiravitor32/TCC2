"""Comportamento do controlador da luminaria (DIVERGENCIAS 71).

Arquitetura de implantacao (Caderno de Encargos, 7.1.1 e 7.2.1): a logica
roda no controlador, e a central so manda comando quando a decisao muda ou
precisa ser renovada. O comando traz o ALVO ja verificado contra o piso, a
taxa maxima de descida da classe e a VALIDADE; o controlador:

  - desce ate o alvo no maximo na taxa da classe, a cada PERIODO_S (a
    descida e calculada pela mesma `verificar` da central: a taxa nao tem
    uma segunda implementacao em Python); sobe na hora;
  - nunca vai abaixo do piso recebido (segunda barreira);
  - vencida a validade sem comando novo, volta ao pleno (RNF07).

Este modulo e puro (sem rede, sem banco, sem relogio proprio): o no simulado
e o executor de cenarios o usam; o firmware do ESP32 implementa o mesmo
comportamento em C++ (firmware/no/no.ino).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .verificacao import PLENO, Criterio, verificar

__all__ = ["Comando", "Controlador", "deve_publicar"]


@dataclass(frozen=True)
class Comando:
    """Carga de iluminacao/{ponto}/comando (Quadro 14, DIVERGENCIAS 71)."""

    decisao_id: str
    nivel: Decimal          # alvo, ja verificado contra o piso
    validade_s: int         # contados a partir do recebimento, no relogio do no
    piso: Decimal           # da classe_iluminacao (RF09), segunda barreira
    taxa_min: Decimal       # decrescimo maximo por minuto

    def carga(self) -> dict:
        return {"decisao_id": self.decisao_id, "nivel": float(self.nivel),
                "validade_s": self.validade_s, "piso": float(self.piso),
                "taxa_min": float(self.taxa_min)}

    @staticmethod
    def de_carga(c: dict) -> "Comando":
        cmd = Comando(str(c["decisao_id"]), Decimal(str(c["nivel"])), int(c["validade_s"]),
                      Decimal(str(c["piso"])), Decimal(str(c["taxa_min"])))
        if not (0 < cmd.validade_s and Decimal(0) <= cmd.nivel <= PLENO):
            raise ValueError(f"comando fora do dominio: {c}")
        return cmd


class Controlador:
    """Estado do no: luz aplicada, alvo e quando o comando vence.

    Liga no pleno (como o firmware): ate o primeiro comando, e no pleno que
    ele fica.
    """

    def __init__(self) -> None:
        self.luz: Decimal = PLENO
        self.comando: Comando | None = None
        self.vence_em: datetime | None = None

    def receber(self, cmd: Comando, agora: datetime) -> None:
        self.comando = cmd
        self.vence_em = agora + timedelta(seconds=cmd.validade_s)

    def vencido(self, agora: datetime) -> bool:
        return self.vence_em is None or agora >= self.vence_em

    def alvo(self, agora: datetime) -> Decimal:
        """Alvo efetivo: o do comando vigente; sem comando vigente, o pleno."""
        if self.comando is None or self.vencido(agora):
            return PLENO
        return self.comando.nivel

    def passo(self, agora: datetime, segundos: float) -> Decimal:
        """Avanca a luz `segundos` em direcao ao alvo e devolve o nivel."""
        alvo = self.alvo(agora)
        if alvo == PLENO:
            # Subir e livre e imediato; o pleno e sempre admissivel.
            self.luz = PLENO
            return self.luz
        crit = Criterio(piso=self.comando.piso, taxa_max_decrescimo_min=self.comando.taxa_min)
        self.luz = verificar(alvo, crit, nivel_anterior=self.luz,
                             segundos_desde_anterior=segundos).nivel_emitido
        return self.luz


def deve_publicar(ultimo: tuple[Decimal, datetime] | None, nivel: Decimal, vence_em: datetime,
                  agora: datetime, renovar_antes_s: float) -> bool:
    """Regra de publicacao da central: so quando muda ou precisa renovar.

    `ultimo` = (alvo, vence_em) do ultimo comando publicado ao ponto. Publica
    se nao houve comando, se o alvo mudou ou se o anterior vence em
    `renovar_antes_s` ou menos E o novo vence depois dele (renovar com o
    dado acabando nao estenderia nada: o no volta ao pleno no vencimento).
    """
    if ultimo is None:
        return True
    nivel_ant, vence_ant = ultimo
    if nivel != nivel_ant:
        return True
    return (vence_ant - agora).total_seconds() <= renovar_antes_s and vence_em > vence_ant
