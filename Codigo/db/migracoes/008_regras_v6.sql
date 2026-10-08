-- Base de regras v6-zurique (DIVERGENCIAS 70). So acrescenta; nada e apagado.
BEGIN;
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v6-zurique', 7,
        'Regras e tercis da v5 (0.0693 e 0.2946) com a rampa = 1/4 da faixa mais estreita (0.0173), regra da v0 (DIVERGENCIAS 70). Arquivo: decisao/regras/v6-zurique.toml.'),
       ('v6-zurique-degraus', 7,
        'Mesma base v6 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;
COMMIT;
