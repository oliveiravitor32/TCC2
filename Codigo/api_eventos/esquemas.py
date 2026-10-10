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

# Dois tipos por trecho de via (DIVERGENCIAS 56):
#   volume     - media de pessoas na area do trecho num periodo (5 min). E a
#                OCUPACAO medida pela contagem instantanea da camera, e nao a
#                soma de passagens: quem vai e volta nao conta duas vezes;
#   ocorrencia - seguranca ou transito, publicada na hora; 'encerrada' fecha
#                a anterior do mesmo trecho.
# A condicao meteorologica nao faz parte do contrato (DIVERGENCIAS 49).
Tipo = Literal["volume", "ocorrencia"]
Abrangencia = Literal["via", "quadra", "bairro", "municipio"]
Ocorrencia = Literal["seguranca", "transito", "encerrada"]


class EventoEntrada(BaseModel):
    """Um item do POST /eventos: o volume ou a ocorrencia de um trecho.

    O corpo do POST e um item ou uma lista de itens (pacote por regiao).
    """

    model_config = ConfigDict(extra="forbid")

    # Volume: fim do periodo medido. Ocorrencia: instante do aviso.
    ocorrido_em: AwareDatetime
    tipo: Tipo
    # Volume: media de pessoas na area no periodo (analitico de contagem por
    # area ja exigido da plataforma, 2.3). Nenhuma identificacao: so o numero.
    pessoas_media: float | None = Field(default=None, ge=0, le=10_000)
    # Volume: duracao do periodo; a especificacao pede 5 min.
    periodo_s: int | None = Field(default=None, ge=1, le=3600)
    ocorrencia: Ocorrencia | None = None
    abrangencia: Abrangencia = "via"
    origem: str = Field(min_length=1, max_length=80)
    # Onde: identificador do trecho de via (segmento de logradouro do
    # GeoSampa). O servico decide para as luminarias associadas a ele
    # (DIVERGENCIAS 54).
    trecho: int = Field(gt=0)
    vigente_ate: AwareDatetime | None = None

    @model_validator(mode="after")
    def _coerente(self) -> EventoEntrada:
        if self.vigente_ate is not None and self.vigente_ate < self.ocorrido_em:
            raise ValueError("'vigente_ate' anterior a 'ocorrido_em'")
        if self.tipo == "volume":
            if self.pessoas_media is None:
                raise ValueError("volume exige 'pessoas_media'")
            if self.ocorrencia is not None:
                raise ValueError("volume nao leva 'ocorrencia': publique-a como tipo 'ocorrencia'")
            if self.periodo_s is None:
                self.periodo_s = 300
        else:
            if self.ocorrencia is None:
                raise ValueError("ocorrencia exige o campo 'ocorrencia'")
            if self.pessoas_media is not None or self.periodo_s is not None:
                raise ValueError("ocorrencia nao leva 'pessoas_media' nem 'periodo_s'")
        return self


class ItemRecusado(BaseModel):
    indice: int
    erro: str


class ResultadoPacote(BaseModel):
    """Resposta do POST /eventos com lista: so o item com erro e recusado."""

    aceitos: list["Evento"]
    recusados: list[ItemRecusado]


class Evento(BaseModel):
    id: int
    ocorrido_em: datetime
    recebido_em: datetime
    tipo: Tipo
    pessoas_media: float | None
    periodo_s: int | None
    ocorrencia: Ocorrencia | None
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
    # O porque (DIVERGENCIAS 55): entradas da inferencia e grau de cada regra.
    entrada: dict | None = None
    ativacoes: dict[str, float] | None = None


class Telemetria(BaseModel):
    """Linha do GET /telemetria (Quadro 14)."""

    decisao_id: UUID
    ponto: str
    medido_em: datetime
    recebido_em: datetime
    duty: float
    lux_medido: float
    # Nivel aplicado ao responder e estado quando o comando chegou, antes de
    # aplica-lo (migracao 010); nulos nos nos antigos.
    nivel_aplicado: float | None = None
    nivel_antes: float | None = None
    lux_antes: float | None = None


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
    nivel_antes: float | None = None
    lux_antes: float | None = None


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


class RegraAtivada(BaseModel):
    id: str
    texto: str
    origem: str
    grau: float


ResultadoPacote.model_rebuild()


class Explicacao(BaseModel):
    """GET /eventos/{id}/explicacao: o que o sistema recebeu e por que decidiu.

    Para cada luminaria do trecho da leitura, a primeira decisao que a usou:
    entradas da inferencia, regras ativadas (texto, origem e grau), nivel
    pretendido, correcao da camada de verificacao e o motivo, nivel emitido
    e o que o sensor mediu.
    """

    evento: Evento
    trecho_nome: str | None
    decisoes: list[dict]


# ---------------------------------------------------------------------------
# Bancada (DIVERGENCIAS 65): conferencia e calibracao gravadas no banco da VM.
# Fora do Quadro 14: e manutencao do no de bancada, nao integracao urbana.
# ---------------------------------------------------------------------------
class SessaoBancadaEntrada(BaseModel):
    """POST /bancada/sessoes: resultado de bancada/conferir.py."""

    model_config = ConfigDict(extra="forbid")

    ponto: str = Field(min_length=1, max_length=40)
    lux_residual: float = Field(ge=0, le=1000)
    aprovada: bool
    observacao: str = Field(max_length=500)


class LinhaCalibracao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    serie: int = Field(ge=1, le=50)
    duty: float = Field(ge=0, le=1)
    lux_medido: float = Field(ge=0, le=100000)


class CalibracaoEntrada(BaseModel):
    """POST /bancada/calibracoes: varredura de bancada/calibrar.py."""

    model_config = ConfigDict(extra="forbid")

    ponto: str = Field(min_length=1, max_length=40)
    lux_residual: float = Field(ge=0, le=1000)
    observacao: str = Field(max_length=500)
    potencia_plena_w: float | None = Field(default=None, gt=0, le=1000)
    linhas: list[LinhaCalibracao] = Field(min_length=1, max_length=2000)


class SessaoBancada(BaseModel):
    sessao_id: int
    descartada: bool
