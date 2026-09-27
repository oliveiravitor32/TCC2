-- Cadastro espacial (DIVERGENCIAS 54), parte 2 de 2. Rodar DEPOIS do
-- db/seed_cadastro.sql. Os eventos anteriores ao cadastro eram todos do ponto
-- de bancada: vao para o trecho principal dele (R. Antonio Viana, 20159).
BEGIN;
UPDATE evento_urbano SET trecho_id = 20159 WHERE trecho_id IS NULL;
ALTER TABLE evento_urbano ALTER COLUMN trecho_id SET NOT NULL;
COMMIT;
