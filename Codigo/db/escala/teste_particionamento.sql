-- Teste do particionamento.sql num banco DESCARTAVEL, ja com schema.sql:
--   createdb teste_particao; psql -d teste_particao -f ../schema.sql
--   psql -d teste_particao -f particionamento.sql -f teste_particionamento.sql
\set ON_ERROR_STOP on
BEGIN;
INSERT INTO trecho_via (id, nome_logradouro, geometria, fonte, extraido_em)
VALUES (999999001, 'Rua Teste', '{}'::jsonb, 'teste', date '2026-11-03');

INSERT INTO escala.evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id)
SELECT t, 'volume', 3, 300, 'teste', 999999001
FROM generate_series(timestamptz '2026-09-01 00:05+00', '2026-11-30 23:55+00', interval '5 min') t;

-- Cada linha caiu na particao do seu mes.
SELECT tableoid::regclass AS particao, count(*) FROM escala.evento_urbano GROUP BY 1 ORDER BY 1;

-- Consulta de um dia le so a particao do mes (poda de particao).
EXPLAIN (COSTS OFF)
SELECT * FROM escala.evento_urbano
WHERE ocorrido_em >= '2026-10-10' AND ocorrido_em < '2026-10-11';

-- Fora da faixa criada: vai para a padrao.
INSERT INTO escala.evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id)
VALUES ('2030-01-01', 'volume', 1, 300, 'teste', 999999001);
SELECT count(*) AS na_padrao FROM escala.evento_urbano_padrao;

-- Retencao: retirar setembro.
SELECT escala.retirar_particao('evento_urbano', date '2026-09-01');
SELECT tableoid::regclass AS particao, count(*) FROM escala.evento_urbano GROUP BY 1 ORDER BY 1;
ROLLBACK;
