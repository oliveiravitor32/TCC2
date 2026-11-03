-- ===========================================================================
-- Particionamento por data de evento_urbano e telemetria (Apendice F do TCC).
--
-- Ilustracao para operacao em escala (3.12.6.4, 3.13.1, 6.1); NAO e usado pelo
-- prototipo, cujo schema.sql segue sem particao. Cria, no schema "escala",
-- versoes particionadas por mes das duas tabelas que crescem com o numero de
-- pontos e com o tempo, ligadas as tabelas do prototipo (trecho_via, decisao,
-- ponto_de_luz). Teste num banco descartavel: teste_particionamento.sql.
--
-- Regra do PostgreSQL que muda o modelo: em tabela particionada, toda chave
-- primaria ou unica tem de conter a coluna de particao. Por isso:
--   * a chave de evento_urbano passa a (id, ocorrido_em), e quem aponta para
--     ele (decisao_evento) leva tambem ocorrido_em;
--   * a telemetria perde o UNIQUE (decisao_id) sozinho: vira UNIQUE
--     (decisao_id, medido_em), e o 1 : 0..1 com a decisao fica a cargo do
--     servico (uma telemetria por decisao_id).
-- ===========================================================================

CREATE SCHEMA IF NOT EXISTS escala;

-- ------------------------------------------------------------ evento_urbano
CREATE TABLE escala.evento_urbano (
    id             BIGINT GENERATED ALWAYS AS IDENTITY,
    ocorrido_em    TIMESTAMPTZ NOT NULL,
    recebido_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    tipo           TEXT NOT NULL CHECK (tipo IN ('volume','ocorrencia')),
    pessoas_media  NUMERIC(8,2) CHECK (pessoas_media >= 0),
    periodo_s      INTEGER CHECK (periodo_s BETWEEN 1 AND 3600),
    ocorrencia     TEXT CHECK (ocorrencia IN ('seguranca','transito','encerrada')),
    abrangencia    TEXT NOT NULL DEFAULT 'via'
                   CHECK (abrangencia IN ('via','quadra','bairro','municipio')),
    origem         TEXT NOT NULL,
    trecho_id      BIGINT NOT NULL REFERENCES public.trecho_via (id),
    vigente_ate    TIMESTAMPTZ,
    CHECK (vigente_ate IS NULL OR vigente_ate >= ocorrido_em),
    CHECK ((tipo = 'volume' AND pessoas_media IS NOT NULL AND periodo_s IS NOT NULL
                            AND ocorrencia IS NULL)
        OR (tipo = 'ocorrencia' AND ocorrencia IS NOT NULL
                            AND pessoas_media IS NULL AND periodo_s IS NULL)),
    PRIMARY KEY (id, ocorrido_em)
) PARTITION BY RANGE (ocorrido_em);

-- Indices criados na tabela-mae valem para cada particao.
CREATE INDEX ON escala.evento_urbano (trecho_id, ocorrido_em DESC);

-- ------------------------------------------------------------ telemetria
CREATE TABLE escala.telemetria (
    id               BIGINT GENERATED ALWAYS AS IDENTITY,
    decisao_id       UUID NOT NULL REFERENCES public.decisao (id),
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES public.ponto_de_luz (id),
    medido_em        TIMESTAMPTZ NOT NULL,
    recebido_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    duty             NUMERIC(5,4) NOT NULL CHECK (duty BETWEEN 0 AND 1),
    lux_medido       NUMERIC(8,2) NOT NULL CHECK (lux_medido >= 0),
    nivel_aplicado   NUMERIC(4,3) CHECK (nivel_aplicado BETWEEN 0 AND 1),
    nivel_antes      NUMERIC(4,3) CHECK (nivel_antes BETWEEN 0 AND 1),
    lux_antes        NUMERIC(8,2) CHECK (lux_antes >= 0),
    PRIMARY KEY (id, medido_em),
    UNIQUE (decisao_id, medido_em)
) PARTITION BY RANGE (medido_em);

CREATE INDEX ON escala.telemetria (ponto_de_luz_id, medido_em DESC);

-- ------------------------------------------------------------ decisao_evento
-- Leva ocorrido_em para poder apontar para a chave composta do evento.
CREATE TABLE escala.decisao_evento (
    decisao_id          UUID        NOT NULL REFERENCES public.decisao (id) ON DELETE CASCADE,
    evento_id           BIGINT      NOT NULL,
    evento_ocorrido_em  TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (decisao_id, evento_id),
    FOREIGN KEY (evento_id, evento_ocorrido_em)
        REFERENCES escala.evento_urbano (id, ocorrido_em)
);

-- ------------------------------------------------------------ particoes
-- Uma particao por mes. Rodar todo mes (cron ou pg_cron) com folga adiante;
-- a particao DEFAULT recebe o que chegar fora das faixas criadas.
CREATE OR REPLACE FUNCTION escala.criar_particoes(tabela TEXT, inicio DATE, meses INT)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    m DATE;
BEGIN
    FOR i IN 0 .. meses - 1 LOOP
        m := (date_trunc('month', inicio) + make_interval(months => i))::date;
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS escala.%I PARTITION OF escala.%I
                 FOR VALUES FROM (%L) TO (%L)',
            tabela || '_' || to_char(m, 'YYYY_MM'), tabela,
            m, (m + interval '1 month')::date);
    END LOOP;
END $$;

CREATE TABLE escala.evento_urbano_padrao PARTITION OF escala.evento_urbano DEFAULT;
CREATE TABLE escala.telemetria_padrao    PARTITION OF escala.telemetria DEFAULT;

SELECT escala.criar_particoes('evento_urbano', date '2026-09-01', 6);
SELECT escala.criar_particoes('telemetria',    date '2026-09-01', 6);

-- ------------------------------------------------------------ retencao
-- Retirar um mes inteiro e operacao de catalogo, sem DELETE linha a linha.
-- Antes, exportar a particao (pg_dump -t) para armazenamento de arquivo.
-- Eventos: a particao so sai depois de retiradas as associacoes de
-- decisao_evento que apontam para ela.
CREATE OR REPLACE FUNCTION escala.retirar_particao(tabela TEXT, mes DATE)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    nome TEXT := tabela || '_' || to_char(mes, 'YYYY_MM');
BEGIN
    EXECUTE format('ALTER TABLE escala.%I DETACH PARTITION escala.%I', tabela, nome);
    EXECUTE format('DROP TABLE escala.%I', nome);
END $$;

-- ------------------------------------------------------------ alternativa
-- Com a extensao TimescaleDB (citada em 3.12.6.4), as particoes por tempo
-- ("chunks") e a retencao sao automaticas. Nao testado (a imagem do
-- prototipo nao tem a extensao):
--   CREATE EXTENSION timescaledb;
--   SELECT create_hypertable('escala.telemetria', 'medido_em',
--                            chunk_time_interval => interval '7 days');
--   SELECT add_retention_policy('escala.telemetria', interval '24 months');
