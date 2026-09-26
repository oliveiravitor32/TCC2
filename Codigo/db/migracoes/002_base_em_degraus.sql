-- Variante em degraus da base v2 (DIVERGENCIAS 43 / 51): mesma base de
-- regras, pertinencias reduzidas a 0 ou 1. So para a comparacao da suite.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v2-sem-meteorologia-degraus', 8,
        'Mesma base v2 como tabela em degraus (corte seco nos tercis, faixa horaria no conjunto de maior grau); so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;
