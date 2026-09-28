-- Leitura do trecho por presenca (DIVERGENCIAS 55). Rodar DEPOIS da 004.
--
-- O evento deixa de ser "movimentacao normalizada" ou "ocorrencia" e passa a
-- ser a LEITURA do trecho: pessoas na area + ocorrencia em curso. Os eventos
-- e decisoes antigos sao de desenvolvimento e teste, e nao se convertem
-- (nivel normalizado nao vira contagem de pessoas): sao apagados, como na
-- migracao 001. Calibracao e sessoes de medicao sao PRESERVADAS.
-- FACA BACKUP ANTES (pg_dump).
BEGIN;

DELETE FROM alerta_diagnostico;
DELETE FROM telemetria;
DELETE FROM decisao_evento;
DELETE FROM decisao;
DELETE FROM execucao_cenario;
DELETE FROM evento_urbano;
UPDATE ponto_de_luz SET estado_operacional = 'operante';

ALTER TABLE evento_urbano DROP CONSTRAINT IF EXISTS evento_urbano_tipo_check;
ALTER TABLE evento_urbano DROP COLUMN valor, DROP COLUMN rotulo;
ALTER TABLE evento_urbano ALTER COLUMN tipo SET DEFAULT 'leitura';
ALTER TABLE evento_urbano ADD CONSTRAINT evento_urbano_tipo_check CHECK (tipo IN ('leitura'));
ALTER TABLE evento_urbano ADD COLUMN pessoas INTEGER NOT NULL CHECK (pessoas >= 0);
ALTER TABLE evento_urbano ADD COLUMN ocorrencia TEXT CHECK (ocorrencia IN ('seguranca','transito'));
DROP INDEX IF EXISTS evento_urbano_tipo_idx;
DROP INDEX IF EXISTS evento_urbano_trecho_idx;
CREATE INDEX evento_urbano_trecho_idx ON evento_urbano (trecho_id, ocorrido_em DESC);

ALTER TABLE trecho_via ADD COLUMN referencia_pessoas NUMERIC(8,2) NOT NULL DEFAULT 5
    CHECK (referencia_pessoas > 0);

ALTER TABLE decisao ADD COLUMN entrada JSONB, ADD COLUMN ativacoes JSONB;

INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v3-presenca', 6,
        'Presenca de pedestre na leitura do trecho em vez de volume observado; 6 regras; tercis de Melbourne na previsao. Arquivo: decisao/regras/v3-presenca.toml.'),
       ('v3-presenca-degraus', 6,
        'Mesma base v3 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;

COMMIT;
