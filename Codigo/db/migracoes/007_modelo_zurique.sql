-- Modelo principal de previsao em 15 min, serie de Zurique (DIVERGENCIAS 69).
-- So acrescenta a versao do modelo e a base de regras v5; nada e apagado.
BEGIN;
INSERT INTO versao_modelo_previsao (rotulo, algoritmo, serie_extraida_em, treinado_em, mae, rmse, hash_modelo)
VALUES ('xgboost-zurique-15min-v1', 'xgboost', '2026-10-01', '2026-10-07', 0.0416, 0.0669,
        '937fcd89f9ec1390ef93be66c2e7b0482113d462411e30c32ac85bf6482971cb')
ON CONFLICT (rotulo) DO UPDATE SET treinado_em = EXCLUDED.treinado_em, mae = EXCLUDED.mae,
    rmse = EXCLUDED.rmse, hash_modelo = EXCLUDED.hash_modelo;
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v5-zurique', 7,
        'As 7 regras da v4 com os tercis de Zurique 15 min (so treino): fronteiras em 0.0693 e 0.2946 (DIVERGENCIAS 69). Arquivo: decisao/regras/v5-zurique.toml.'),
       ('v5-zurique-degraus', 7,
        'Mesma base v5 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;
COMMIT;
