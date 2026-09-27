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

Tipo = Literal["movimentacao", "ocorrencia"]
Abrangencia = Literal["via", "quadra", "bairro", "municipio"]

# Rotulos admitidos por tipo. "encerrada" existe para que a plataforma possa
# declarar o FIM de uma ocorrencia, e nao so o inicio. A condicao
# meteorologica nao faz parte do contrato: a plataforma de monitoramento nao
# a produz (DIVERGENCIAS 49).
ROTULOS: dict[str, frozenset[str]] = {
    "ocorrencia": frozenset({"seguranca", "transito", "encerrada"}),
}


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
    # Onde: identificador do trecho de via (segmento de logradouro do
    # GeoSampa). Um evento se refere a um trecho; o servico decide para as
    # luminarias associadas a ele (DIVERGENCIAS 54).
    trecho: int = Field(gt=0)
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
    trecho: int
    vigente_ate: datetime | None


class Decisao(BaseModel):
    """Linha do GET /decisoes (Quadro 14)."""

    id: UUID
    criado_em: datetime
    ponto: str
    classe_codigo: str
    nivel_pretendido: float
    nivel_emitido: float
    restricao_aplicada: Literal["nenhuma", "piso", "taxa"]
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


class Ponto(BaseModel):
    """Linha do GET /pontos: estado atual do ponto de luz, para o painel."""

    codigo: str
    placa: str | None
    logradouro: str | None
    trechos: list[int]
    classe_codigo: str
    estado_operacional: Literal["operante", "falha", "manutencao", "sem_comunicacao"]
    lux_pleno: float
    piso_fracao: float | None
    nivel_emitido: float | None
    restricao_aplicada: str | None
    decidido_em: datetime | None
    lux_medido: float | None
    duty: float | None
    medido_em: datetime | None


class Alerta(BaseModel):
    """Linha do GET /alertas (RF11, 3.4.5)."""

    id: int
    ponto: str
    tipo: Literal["falha_total", "perda_controle"]
    razao: float | None
    tolerancia: float | None
    ciclos: int | None
    aberto_em: datetime
    encerrado_em: datetime | None


class AmostraEnergia(BaseModel):
    """Um instante da serie de potencia (RF12)."""

    medido_em: datetime
    # Fracao do fluxo pleno pela LUZ MEDIDA e pelo COMANDO: 3.11 manda
    # confrontar as duas estimativas.
    fracao_medida: float
    fracao_comandada: float
    potencia_medida_w: float
    potencia_comandada_w: float


class Energia(BaseModel):
    """GET /energia: consumo estimado na janela, para a luminaria de referencia.

    Estimativa, nao medicao eletrica (3.11): supoe potencia proporcional ao
    nivel e despreza o consumo fixo do driver e do controlador, o que a torna
    um limite superior otimista.
    """

    ponto: str
    luminaria: str
    potencia_nominal_w: float
    janela_min: float
    inicio: datetime
    fim: datetime
    amostras: list[AmostraEnergia]
    potencia_agora_w: float | None
    energia_pela_luz_wh: float
    energia_pelo_comando_wh: float
    energia_pleno_wh: float
    energia_horario_fixo_wh: float
    razao_pleno: float | None
    razao_horario_fixo: float | None
    divergencia_entre_estimativas: float | None


class Trecho(BaseModel):
    """Linha do GET /trechos: trecho de via e as luminarias associadas."""

    id: int
    codlog: str | None
    tipo_logradouro: str | None
    nome_logradouro: str
    numero_inicial: int | None
    numero_final: int | None
    pontos: list[str]
