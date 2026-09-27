-- Cadastro espacial (DIVERGENCIAS 54), parte 1 de 2: estrutura.
-- Ordem para um banco que ja existe (local ou VM):
--   1. este arquivo
--   2. db/seed_cadastro.sql      (trechos reais, pontos e associacoes)
--   3. db/migracoes/004_evento_trecho_obrigatorio.sql
-- Banco novo nao precisa: schema.sql e seed_cadastro.sql ja rodam na criacao.
BEGIN;

CREATE TABLE trecho_via (
    id               BIGINT PRIMARY KEY,
    codlog           TEXT,
    tipo_logradouro  TEXT,
    nome_logradouro  TEXT NOT NULL,
    numero_inicial   INTEGER,
    numero_final     INTEGER,
    geometria        JSONB NOT NULL,
    fonte            TEXT NOT NULL,
    extraido_em      DATE NOT NULL
);

ALTER TABLE ponto_de_luz
    ADD COLUMN placa TEXT UNIQUE,
    ADD COLUMN utm_e NUMERIC(11,2),
    ADD COLUMN utm_n NUMERIC(11,2);

CREATE TABLE trecho_ponto (
    trecho_id        BIGINT NOT NULL REFERENCES trecho_via (id),
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    distancia_m      NUMERIC(6,2) NOT NULL CHECK (distancia_m >= 0),
    criterio         TEXT NOT NULL,
    associado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (trecho_id, ponto_de_luz_id)
);
CREATE INDEX trecho_ponto_ponto_idx ON trecho_ponto (ponto_de_luz_id);

-- Nulo por enquanto: a parte 2 atribui os eventos antigos e torna obrigatorio.
ALTER TABLE evento_urbano ADD COLUMN trecho_id BIGINT REFERENCES trecho_via (id);
CREATE INDEX evento_urbano_trecho_idx ON evento_urbano (trecho_id, tipo, ocorrido_em DESC);

COMMIT;
