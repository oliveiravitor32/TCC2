-- Estado do no ANTES de aplicar o comando (decisao do autor, 11/10/2026).
-- A telemetria e a primeira leitura depois de aplicar; sem isto, o ponto onde
-- a rampa anterior chegou (o piso, por exemplo) nunca ficava no banco, so na
-- serial do no. O no envia, junto da leitura nova, o nivel que aplicava e o
-- ultimo lux medido no instante em que o comando chegou. So acrescenta colunas;
-- nos antigos nao enviam e as colunas ficam nulas.
BEGIN;

ALTER TABLE telemetria ADD COLUMN IF NOT EXISTS nivel_antes NUMERIC(4,3)
    CHECK (nivel_antes BETWEEN 0 AND 1);
ALTER TABLE telemetria ADD COLUMN IF NOT EXISTS lux_antes NUMERIC(8,2)
    CHECK (lux_antes >= 0);

COMMIT;
