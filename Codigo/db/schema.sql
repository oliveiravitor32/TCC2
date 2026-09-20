-- Iluminacao Adaptativa - esquema do banco (TCC 7.2.2, Quadro 2, 8.5)
-- PostgreSQL 16+
-- Nenhuma entidade guarda imagem, audio ou identificador individual (RNF08).

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- Referencia normativa (RF09): os limites da ABNT NBR 5101 ficam em tabela,
-- nunca no codigo. A camada de verificacao le seu criterio daqui.
-- ---------------------------------------------------------------------------
CREATE TABLE classe_iluminacao (
    codigo                     TEXT PRIMARY KEY,
    descricao                  TEXT NOT NULL,
    iluminancia_media_min_lux  NUMERIC(6,2) NOT NULL CHECK (iluminancia_media_min_lux > 0),
    iluminancia_min_lux        NUMERIC(6,2) NOT NULL CHECK (iluminancia_min_lux > 0),
    iluminancia_vert_min_lux   NUMERIC(6,2) NOT NULL CHECK (iluminancia_vert_min_lux > 0),
    -- Classe mais baixa ate a qual a dimerizacao e admitida (NBR 5101, 6.10:
    -- no maximo duas classes imediatamente inferiores). NULL = nao dimerizavel.
    classe_min_dimerizacao     TEXT REFERENCES classe_iluminacao (codigo),
    -- Fracao do fluxo pleno por minuto; limita apenas o DECRESCIMO.
    taxa_max_decrescimo_min    NUMERIC(4,3) NOT NULL
                               CHECK (taxa_max_decrescimo_min > 0 AND taxa_max_decrescimo_min <= 1),
    fonte_normativa            TEXT NOT NULL DEFAULT 'ABNT NBR 5101:2024',
    criado_em                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE classe_iluminacao IS
    'Criterio normativo externo consultado pela camada de verificacao (RF09).';
COMMENT ON COLUMN classe_iluminacao.classe_min_dimerizacao IS
    'Piso admissivel: a fracao de fluxo pleno e a razao entre as iluminancias medias.';

-- ---------------------------------------------------------------------------
-- Ponto de luz. Na bancada existe um unico registro; o modelo e o do parque.
-- ---------------------------------------------------------------------------
CREATE TABLE ponto_de_luz (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo              TEXT NOT NULL UNIQUE,
    logradouro          TEXT,
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    classe_codigo       TEXT NOT NULL REFERENCES classe_iluminacao (codigo),
    estado_operacional  TEXT NOT NULL DEFAULT 'operante'
                        CHECK (estado_operacional IN ('operante','falha','manutencao','sem_comunicacao')),
    -- Potencia do segmento de fita a ciclo pleno, medida em bancada (7.3.2).
    -- Base da estimativa de energia (RF12); nao e medicao eletrica.
    potencia_plena_w    NUMERIC(7,2) CHECK (potencia_plena_w > 0),
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Eventos recebidos da interface de dados urbanos (REST).
-- ---------------------------------------------------------------------------
CREATE TABLE evento_urbano (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ocorrido_em  TIMESTAMPTZ NOT NULL,
    recebido_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    tipo         TEXT NOT NULL CHECK (tipo IN ('movimentacao','ocorrencia','meteorologia')),
    valor        NUMERIC(10,3),
    -- Rotulo textual: 'chuva', 'neblina', 'nevoeiro', 'acidente', 'limpo'...
    rotulo       TEXT,
    abrangencia  TEXT NOT NULL DEFAULT 'via'
                 CHECK (abrangencia IN ('via','quadra','bairro','municipio')),
    origem       TEXT NOT NULL,
    -- Ate quando o evento permanece vigente para o ciclo de decisao.
    vigente_ate  TIMESTAMPTZ,
    CHECK (vigente_ate IS NULL OR vigente_ate >= ocorrido_em)
);

CREATE INDEX evento_urbano_ocorrido_idx ON evento_urbano (ocorrido_em DESC);
CREATE INDEX evento_urbano_tipo_idx     ON evento_urbano (tipo, ocorrido_em DESC);

-- ---------------------------------------------------------------------------
-- Versao da base de regras Mamdani: condicao para reproduzir resultados.
-- ---------------------------------------------------------------------------
CREATE TABLE versao_base_regras (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rotulo         TEXT NOT NULL UNIQUE,
    vigente_desde  TIMESTAMPTZ NOT NULL DEFAULT now(),
    qtd_regras     INTEGER NOT NULL CHECK (qtd_regras > 0),
    resumo         TEXT NOT NULL,
    -- Hash do arquivo de regras, para detectar edicao sem nova versao.
    hash_regras    TEXT
);

-- ---------------------------------------------------------------------------
-- Decisao: nucleo do registro de auditoria. Separar nivel_pretendido de
-- nivel_emitido e o que torna mensuravel a camada de verificacao.
-- ---------------------------------------------------------------------------
CREATE TABLE decisao (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criado_em              TIMESTAMPTZ NOT NULL DEFAULT now(),
    ponto_de_luz_id        BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    versao_base_regras_id  BIGINT NOT NULL REFERENCES versao_base_regras (id),
    -- Classe vigente no momento da decisao: congela o criterio aplicado
    -- mesmo que a via seja reclassificada depois (8.5).
    classe_codigo          TEXT NOT NULL REFERENCES classe_iluminacao (codigo),
    -- Entrada da inferencia: saida da camada de previsao.
    previsao_movimentacao  NUMERIC(10,3),
    -- Fracao do fluxo pleno. 1,000 = 10 lux (P3); 0,500 = 5 lux (P5).
    nivel_pretendido       NUMERIC(4,3) NOT NULL CHECK (nivel_pretendido BETWEEN 0 AND 1),
    nivel_emitido          NUMERIC(4,3) NOT NULL CHECK (nivel_emitido    BETWEEN 0 AND 1),
    -- Qual regra da camada de verificacao corrigiu o nivel pretendido.
    restricao_aplicada     TEXT NOT NULL DEFAULT 'nenhuma'
                           CHECK (restricao_aplicada IN ('nenhuma','piso','taxa','meteorologia')),
    -- Nivel emitido na decisao anterior, base do limite de taxa.
    nivel_anterior         NUMERIC(4,3) CHECK (nivel_anterior BETWEEN 0 AND 1),
    publicado_em           TIMESTAMPTZ,
    -- Invariante estrutural: correcao registrada <=> nivel alterado.
    CHECK ((restricao_aplicada = 'nenhuma') = (nivel_emitido = nivel_pretendido))
);

CREATE INDEX decisao_ponto_tempo_idx ON decisao (ponto_de_luz_id, criado_em DESC);
CREATE INDEX decisao_restricao_idx   ON decisao (restricao_aplicada)
    WHERE restricao_aplicada <> 'nenhuma';

-- Entidade associativa (8.5): uma decisao apoia-se em varios eventos e um
-- evento sustenta decisoes sucessivas enquanto permanecer vigente.
CREATE TABLE decisao_evento (
    decisao_id  UUID   NOT NULL REFERENCES decisao (id) ON DELETE CASCADE,
    evento_id   BIGINT NOT NULL REFERENCES evento_urbano (id),
    PRIMARY KEY (decisao_id, evento_id)
);

CREATE INDEX decisao_evento_evento_idx ON decisao_evento (evento_id);

-- ---------------------------------------------------------------------------
-- Telemetria: 1:1 com a decisao (8.5). Leituras periodicas que nao
-- correspondam a comando nao sao registradas aqui.
-- ---------------------------------------------------------------------------
CREATE TABLE telemetria (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    decisao_id       UUID NOT NULL UNIQUE REFERENCES decisao (id),
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    medido_em        TIMESTAMPTZ NOT NULL,
    recebido_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Ciclo de trabalho aplicado, 0..1 (PWM de 12 bits no no).
    duty             NUMERIC(5,4) NOT NULL CHECK (duty BETWEEN 0 AND 1),
    lux_medido       NUMERIC(8,2) NOT NULL CHECK (lux_medido >= 0)
);

CREATE INDEX telemetria_ponto_tempo_idx ON telemetria (ponto_de_luz_id, medido_em DESC);

-- ---------------------------------------------------------------------------
-- Visao de auditoria: cadeia evento -> decisao -> medicao, com a latencia do
-- percurso e a divergencia entre nivel decidido e nivel entregue.
-- ---------------------------------------------------------------------------
CREATE VIEW auditoria_decisao AS
SELECT d.id                          AS decisao_id,
       d.criado_em,
       p.codigo                      AS ponto,
       d.classe_codigo,
       c.iluminancia_media_min_lux   AS lux_pleno,
       cm.iluminancia_media_min_lux / c.iluminancia_media_min_lux AS piso_fracao,
       d.nivel_pretendido,
       d.nivel_emitido,
       d.restricao_aplicada,
       t.duty,
       t.lux_medido,
       t.lux_medido - (d.nivel_emitido * c.iluminancia_media_min_lux) AS divergencia_lux,
       t.recebido_em - d.criado_em   AS latencia
  FROM decisao d
  JOIN ponto_de_luz p      ON p.id     = d.ponto_de_luz_id
  JOIN classe_iluminacao c ON c.codigo = d.classe_codigo
  LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
  LEFT JOIN telemetria t   ON t.decisao_id = d.id;

COMMIT;
