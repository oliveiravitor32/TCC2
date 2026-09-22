"""Contrato de dados da interface de dados urbanos (TCC 4.6.2, Quadro 14).

A especificacao desta interface e, ela propria, resultado do trabalho
(objetivo f): define o que uma plataforma municipal precisaria publicar.
Por isso o vocabulario e fechado e qualquer campo fora do contrato e
recusado - identificadores, imagens e placas nao cabem nele (RNF08, 3.10).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Tipo = Literal["movimentacao", "ocorrencia", "meteorologia"]
Abrangencia = Literal["via", "quadra", "bairro", "municipio"]

# Rotulos admitidos por tipo. "limpo" e "encerrada" existem para que a
# plataforma possa declarar o FIM de uma condicao, e nao so o inicio.
ROTULOS: dict[str, frozenset[str]] = {
    "meteorologia": frozenset({"chuva", "neblina", "nevoeiro", "limpo"}),
    "ocorrencia": frozenset({"seguranca", "transito", "encerrada"}),
}
# Condicoes em que a NBR 5101 (6.10) desaconselha dimerizar.
METEOROLOGIA_ADVERSA: frozenset[str] = frozenset({"chuva", "neblina", "nevoeiro"})


class EventoEntrada(BaseModel):
    """Corpo do POST /eventos."""

    model_config = ConfigDict(extra="forbid")

    ocorrido_em: AwareDatetime
    tipo: Tipo
    # Movimentacao normalizada no ponto: 0 = minimo, 1 = maximo historico.
    valor: float | None = Field(default=None, ge=0, le=1)
    rotulo: str | None = None
    abrangencia: Abrangencia = "via"
    origem: str = Field(min_length=1, max_length=80)
    vigente_ate: AwareDatetime | None = None

    @model_validator(mode="after")
    def _coerente_com_o_tipo(self) -> EventoEntrada:
        if self.tipo == "movimentacao":
            if self.valor is None:
                raise ValueError("movimentacao exige 'valor' em [0,1]")
            if self.rotulo is not None:
                raise ValueError("movimentacao nao admite 'rotulo'")
        else:
            if self.rotulo not in ROTULOS[self.tipo]:
                admitidos = ", ".join(sorted(ROTULOS[self.tipo]))
                raise ValueError(f"{self.tipo} exige 'rotulo' em: {admitidos}")
            if self.valor is not None:
                raise ValueError(f"{self.tipo} nao admite 'valor'")
        if self.vigente_ate is not None and self.vigente_ate < self.ocorrido_em:
            raise ValueError("'vigente_ate' anterior a 'ocorrido_em'")
        return self


class Evento(BaseModel):
    id: int
    ocorrido_em: datetime
    recebido_em: datetime
    tipo: Tipo
    valor: float | None
    rotulo: str | None
    abrangencia: Abrangencia
    origem: str
    vigente_ate: datetime | None


class Decisao(BaseModel):
    """Linha do GET /decisoes (Quadro 14)."""

    id: UUID
    criado_em: datetime
    ponto: str
    classe_codigo: str
    nivel_pretendido: float
    nivel_emitido: float
    restricao_aplicada: Literal["nenhuma", "piso", "taxa", "meteorologia"]
    nivel_anterior: float | None
    previsao_movimentacao: float | None
    versao_base_regras: str
    versao_modelo: str
    execucao_id: int | None
    evento_ids: list[int]


class Telemetria(BaseModel):
    """Linha do GET /telemetria (Quadro 14)."""

    decisao_id: UUID
    ponto: str
    medido_em: datetime
    recebido_em: datetime
    duty: float
    lux_medido: float
