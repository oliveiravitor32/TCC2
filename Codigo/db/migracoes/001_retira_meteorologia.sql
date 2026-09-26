-- Migracao 001: retirada da condicao meteorologica (DIVERGENCIAS 49).
--
-- Para um banco criado ANTES da mudanca. Um banco novo ja nasce certo pelo
-- schema.sql e pelo seed.sql.
--
-- Apaga os registros de desenvolvimento (eventos, decisoes, telemetria,
-- alertas e execucoes de cenario), que usavam 'meteorologia' e seriam
-- recusados pelas restricoes novas. PRESERVA a calibracao da bancada
-- (sessao_medicao e calibracao), que vem de medicao real. Faca backup antes:
--   docker compose exec -T db pg_dump -U iluminacao -d iluminacao > backups/antes.sql

BEGIN;

DELETE FROM alerta_diagnostico;
DELETE FROM telemetria;
DELETE FROM decisao_evento;
DELETE FROM decisao;
DELETE FROM execucao_cenario;
DELETE FROM evento_urbano;
UPDATE ponto_de_luz SET estado_operacional = 'operante'
 WHERE estado_operacional IN ('falha', 'sem_comunicacao');

ALTER TABLE evento_urbano DROP CONSTRAINT IF EXISTS evento_urbano_tipo_check;
ALTER TABLE evento_urbano ADD CONSTRAINT evento_urbano_tipo_check
    CHECK (tipo IN ('movimentacao','ocorrencia'));

ALTER TABLE decisao DROP CONSTRAINT IF EXISTS decisao_restricao_aplicada_check;
ALTER TABLE decisao ADD CONSTRAINT decisao_restricao_aplicada_check
    CHECK (restricao_aplicada IN ('nenhuma','piso','taxa'));

INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v2-sem-meteorologia', 8,
        'Tercis da serie de Melbourne (2026-09-23): fronteiras em 0.1038 e 0.4053; '
        '8 regras, sem condicao meteorologica. Arquivo: decisao/regras/v2-sem-meteorologia.toml.')
ON CONFLICT (rotulo) DO NOTHING;

COMMIT;
