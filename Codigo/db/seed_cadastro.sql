-- Cadastro espacial (DIVERGENCIAS 54). GERADO por `python -m cadastro.recorte sql`;
-- nao editar a mao. Fonte: GeoSampa (Prefeitura de Sao Paulo), servico WFS publico, extraido em 2026-09-27.
-- Trechos = segmentos de logradouro; pontos = postes reais (placa), EPSG:31983.

INSERT INTO trecho_via (id, codlog, tipo_logradouro, nome_logradouro,
                        numero_inicial, numero_final, geometria, fonte, extraido_em) VALUES
  (1411, NULL, NULL, 'SEM DENOMINACAO', 0, 59, '{"type": "LineString", "coordinates": [[354637.96, 7402017.35], [354575.52, 7402012.35]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (4645, '026301', 'R', 'AVELINO MATOS MACHADO', 0, 53, '{"type": "LineString", "coordinates": [[354637.96, 7402017.35], [354638.06, 7402017.36], [354648.09, 7402017.66], [354690.66, 7402021.26]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (4646, '026301', 'R', 'AVELINO MATOS MACHADO', 52, 113, '{"type": "LineString", "coordinates": [[354690.66, 7402021.26], [354746.05, 7402025.95]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (18459, '317020', 'TV', 'SUDAO', 0, 121, '{"type": "LineString", "coordinates": [[354682.71, 7402143.75], [354682.57, 7402135.1], [354684.97, 7402104.98], [354690.66, 7402021.26]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (18570, '603465', 'R', 'VINHAIS', 0, 103, '{"type": "LineString", "coordinates": [[354750.32, 7401968.01], [354643.11, 7401959.84]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (18571, '784664', 'R', 'CARMO DE MINAS', 0, 109, '{"type": "LineString", "coordinates": [[354569.15, 7401982.71], [354580.24, 7401872.01]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (19319, '039900', 'R', 'CAMOES', 0, 105, '{"type": "LineString", "coordinates": [[354754.92, 7401913.52], [354748.4, 7401912.04], [354647.9, 7401903.5]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (19400, '782343', 'R', 'VARZEA DA PALMA', 152, 329, '{"type": "LineString", "coordinates": [[354456.25, 7402048.11], [354558.05, 7402056.71], [354633.85, 7402063.11]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20121, '023965', 'R', 'ASCENSO FERNANDES', 968, 1023, '{"type": "LineString", "coordinates": [[354643.11, 7401959.84], [354647.9, 7401903.5]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20159, '018902', 'R', 'ANTONIO VIANA', 1128, 1199, '{"type": "LineString", "coordinates": [[354569.15, 7401982.71], [354640.53, 7401988.75]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20345, '018902', 'R', 'ANTONIO VIANA', 1022, 1129, '{"type": "LineString", "coordinates": [[354463.27, 7401973.73], [354569.15, 7401982.71]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20799, '023965', 'R', 'ASCENSO FERNANDES', 862, 909, '{"type": "LineString", "coordinates": [[354633.85, 7402063.11], [354637.37, 7402023.9], [354637.96, 7402017.35]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20800, '023965', 'R', 'ASCENSO FERNANDES', 788, 863, '{"type": "LineString", "coordinates": [[354627.28, 7402139.28], [354630.18, 7402103.86], [354633.85, 7402063.11]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (20802, '023965', 'R', 'ASCENSO FERNANDES', 1022, 1049, '{"type": "LineString", "coordinates": [[354647.9, 7401903.5], [354648.48, 7401896.65], [354649.99, 7401878.22]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (21198, '023965', 'R', 'ASCENSO FERNANDES', 908, 939, '{"type": "LineString", "coordinates": [[354637.96, 7402017.35], [354640.53, 7401988.75]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27'),
  (22661, '023965', 'R', 'ASCENSO FERNANDES', 938, 969, '{"type": "LineString", "coordinates": [[354640.53, 7401988.75], [354642.74, 7401964.19], [354643.11, 7401959.84]]}'::jsonb, 'GeoSampa segmento_logradouro', '2026-09-27')
ON CONFLICT (id) DO NOTHING;

-- Pontos com no: codigo do sistema -> poste real do recorte.
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n)
VALUES ('BANCADA-01', 'RUA ANTONIO VIANA', 'P3', 'IP0412418', 354624.63, 7401981.80)
ON CONFLICT (codigo) DO UPDATE SET placa = EXCLUDED.placa, logradouro = EXCLUDED.logradouro,
    utm_e = EXCLUDED.utm_e, utm_n = EXCLUDED.utm_n;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n)
VALUES ('SIMULADO-02', 'RUA VARZEA DA PALMA', 'P3', 'IP0412401', 354588.61, 7402056.85)
ON CONFLICT (codigo) DO UPDATE SET placa = EXCLUDED.placa, logradouro = EXCLUDED.logradouro,
    utm_e = EXCLUDED.utm_e, utm_n = EXCLUDED.utm_n;

-- Associacao trecho x ponto: distancia a linha do trecho <= 25 m (EPSG:31983).
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19400, id, 2.43, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'SIMULADO-02'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 5.59, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'BANCADA-01'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 22661, id, 16.46, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'BANCADA-01'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 17.35, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'BANCADA-01'
ON CONFLICT DO NOTHING;
