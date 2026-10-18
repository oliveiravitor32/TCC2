-- Grupo de controle e visao de bairro (DIVERGENCIAS 76, 18/10/2026).
-- Grupo = pontos associados exatamente aos mesmos trechos e da mesma classe:
-- recebem a mesma decisao, calculada uma vez. So acrescenta; nada muda nos
-- registros existentes. Depois de aplicar: python -m decisao.grupos
BEGIN;

CREATE TABLE IF NOT EXISTS grupo_controle (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chave          TEXT NOT NULL UNIQUE,
    classe_codigo  TEXT NOT NULL REFERENCES classe_iluminacao (codigo),
    trechos        BIGINT[] NOT NULL,
    calculado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE ponto_de_luz ADD COLUMN IF NOT EXISTS simulado BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE ponto_de_luz ADD COLUMN IF NOT EXISTS grupo_id BIGINT REFERENCES grupo_controle (id);
ALTER TABLE decisao ADD COLUMN IF NOT EXISTS grupo_id BIGINT REFERENCES grupo_controle (id);
ALTER TABLE trecho_via ADD COLUMN IF NOT EXISTS geometria_wgs84 JSONB;

COMMIT;
