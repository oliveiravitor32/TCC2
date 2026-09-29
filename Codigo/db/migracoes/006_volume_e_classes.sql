-- Volume de movimento e saida em degraus de classe (DIVERGENCIAS 56).
-- Rodar DEPOIS da 005.
--
-- A plataforma deixa de publicar a leitura instantanea do trecho (pessoas
-- agora + ocorrencia) e passa a publicar dois tipos: o VOLUME (media de
-- pessoas na area num periodo de 5 min) e a OCORRENCIA (na hora; 'encerrada'
-- fecha a anterior). As leituras e decisoes antigas sao de desenvolvimento e
-- teste e nao se convertem (contagem instantanea nao e media de periodo):
-- sao apagadas, como nas migracoes 001 e 005. Calibracao e sessoes de
-- medicao sao PRESERVADAS.
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
ALTER TABLE evento_urbano DROP CONSTRAINT IF EXISTS evento_urbano_ocorrencia_check;
ALTER TABLE evento_urbano DROP COLUMN pessoas;
ALTER TABLE evento_urbano ALTER COLUMN tipo DROP DEFAULT;
ALTER TABLE evento_urbano ADD CONSTRAINT evento_urbano_tipo_check
    CHECK (tipo IN ('volume','ocorrencia'));
ALTER TABLE evento_urbano ADD COLUMN pessoas_media NUMERIC(8,2) CHECK (pessoas_media >= 0);
ALTER TABLE evento_urbano ADD COLUMN periodo_s INTEGER CHECK (periodo_s BETWEEN 1 AND 3600);
ALTER TABLE evento_urbano ADD CONSTRAINT evento_urbano_ocorrencia_check
    CHECK (ocorrencia IN ('seguranca','transito','encerrada'));
ALTER TABLE evento_urbano ADD CONSTRAINT evento_urbano_tipo_campos_check
    CHECK ((tipo = 'volume' AND pessoas_media IS NOT NULL AND periodo_s IS NOT NULL
                            AND ocorrencia IS NULL)
        OR (tipo = 'ocorrencia' AND ocorrencia IS NOT NULL
                            AND pessoas_media IS NULL AND periodo_s IS NULL));

INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v4-volume', 7,
        'Volume de movimento (media de 5 min por trecho) observado e previsto; 7 regras; saida em degraus de classe lidos de classe_iluminacao. Arquivo: decisao/regras/v4-volume.toml.'),
       ('v4-volume-degraus', 7,
        'Mesma base v4 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;

COMMIT;
