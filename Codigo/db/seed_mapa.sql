-- Visao de bairro (DIVERGENCIAS 76). GERADO por `python -m cadastro.mapa`; nao editar a mao.
-- Nos SIMULADOS (lux sintetico, simulado = true): so para a demonstracao, nunca resultado.
-- Depois de aplicar: python -m decisao.grupos
BEGIN;

-- Coordenadas WGS84 dos trechos, so para o mapa do painel.
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234631, -23.4854713], [-46.4240749, -23.4855109]]}'::jsonb WHERE id = 1411;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234631, -23.4854713], [-46.4234621, -23.4854712], [-46.4233639, -23.4854694], [-46.4229468, -23.4854407]]}'::jsonb WHERE id = 4645;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4229468, -23.4854407], [-46.422404, -23.4854033]]}'::jsonb WHERE id = 4646;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4230127, -23.4843339], [-46.423015, -23.484412], [-46.4229943, -23.4846842], [-46.4229468, -23.4854407]]}'::jsonb WHERE id = 18459;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4223679, -23.4859269], [-46.4234182, -23.4859911]]}'::jsonb WHERE id = 18570;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4241401, -23.485778], [-46.4240422, -23.4867785]]}'::jsonb WHERE id = 18571;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4223281, -23.4864193], [-46.4223921, -23.4864321], [-46.4233768, -23.4865002]]}'::jsonb WHERE id = 19319;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4252391, -23.4851772], [-46.4242416, -23.4851087], [-46.4234989, -23.4850577]]}'::jsonb WHERE id = 19400;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234182, -23.4859911], [-46.4233768, -23.4865002]]}'::jsonb WHERE id = 20121;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4241401, -23.485778], [-46.4234407, -23.4857297]]}'::jsonb WHERE id = 20159;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4251776, -23.4858495], [-46.4241401, -23.485778]]}'::jsonb WHERE id = 20345;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234989, -23.4850577], [-46.4234682, -23.4854121], [-46.4234631, -23.4854713]]}'::jsonb WHERE id = 20799;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4235558, -23.4843693], [-46.4235308, -23.4846894], [-46.4234989, -23.4850577]]}'::jsonb WHERE id = 20800;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4233768, -23.4865002], [-46.4233717, -23.4865621], [-46.4233588, -23.4867287]]}'::jsonb WHERE id = 20802;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234631, -23.4854713], [-46.4234407, -23.4857297]]}'::jsonb WHERE id = 21198;
UPDATE trecho_via SET geometria_wgs84 = '{"type": "LineString", "coordinates": [[-46.4234407, -23.4857297], [-46.4234214, -23.4859518], [-46.4234182, -23.4859911]]}'::jsonb WHERE id = 22661;

-- Pontos que ja tem no (BANCADA-01, SIMULADO-02): so as coordenadas.
UPDATE ponto_de_luz SET latitude = -23.485791, longitude = -46.423597 WHERE codigo = 'BANCADA-01';
UPDATE ponto_de_luz SET latitude = -23.485110, longitude = -46.423942 WHERE codigo = 'SIMULADO-02';

-- 33 postes reais do recorte como nos simulados.
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410150', 'RUA CAMOES', 'P3', 'IP0410150', 354698.60, 7401904.24, -23.486498, -46.422880, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410152', 'RUA CAMOES', 'P3', 'IP0410152', 354662.63, 7401901.06, -23.486524, -46.423233, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410153', 'RUA ASCENSO FERNANDES', 'P3', 'IP0410153', 354651.72, 7401923.07, -23.486324, -46.423338, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410154', 'RUA CAMOES', 'P3', 'IP0410154', 354654.58, 7401900.62, -23.486527, -46.423312, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410155', 'RUA SILVEIRA PIRES', 'P3', 'IP0410155', 354641.51, 7401885.03, -23.486666, -46.423441, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410156', 'RUA SILVEIRA PIRES', 'P3', 'IP0410156', 354606.16, 7401881.59, -23.486694, -46.423788, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410182', 'RUA CARMO DE MINAS', 'P3', 'IP0410182', 354575.11, 7401887.37, -23.486639, -46.424091, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410183', 'RUA CARMO DE MINAS', 'P3', 'IP0410183', 354573.06, 7401909.83, -23.486436, -46.424109, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0410184', 'RUA CARMO DE MINAS', 'P3', 'IP0410184', 354571.01, 7401934.33, -23.486215, -46.424127, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0411799', 'RUA ASCENSO FERNANDES', 'P3', 'IP0411799', 354640.14, 7402060.86, -23.485079, -46.423438, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0411800', 'RUA VARZEA DA PALMA', 'P3', 'IP0411800', 354621.54, 7402059.72, -23.485087, -46.423620, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412402', 'RUA VARZEA DA PALMA', 'P3', 'IP0412402', 354559.34, 7402053.82, -23.485135, -46.424229, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412403', 'RUA VARZEA DA PALMA', 'P3', 'IP0412403', 354531.89, 7402051.28, -23.485155, -46.424498, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412414', 'RUA ANTONIO VIANA', 'P3', 'IP0412414', 354531.69, 7401973.44, -23.485858, -46.424508, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412415', 'RUA CARMO DE MINAS', 'P3', 'IP0412415', 354565.66, 7401976.59, -23.485833, -46.424175, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412416', 'RUA CARMO DE MINAS', 'P3', 'IP0412416', 354567.74, 7401968.45, -23.485907, -46.424155, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412417', 'RUA ANTONIO VIANA', 'P3', 'IP0412417', 354585.96, 7401978.17, -23.485820, -46.423976, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412419', 'RUA ASCENSO FERNANDES', 'P3', 'IP0412419', 354647.73, 7401967.13, -23.485926, -46.423372, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412420', 'RUA VINHAIS', 'P3', 'IP0412420', 354652.73, 7401964.58, -23.485949, -46.423324, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412421', 'RUA VINHAIS', 'P3', 'IP0412421', 354678.55, 7401966.76, -23.485932, -46.423071, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412422', 'RUA VINHAIS', 'P3', 'IP0412422', 354711.50, 7401969.43, -23.485911, -46.422748, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412423', 'RUA ASCENSO FERNANDES', 'P3', 'IP0412423', 354646.09, 7401984.10, -23.485772, -46.423387, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412424', 'RUA ASCENSO FERNANDES', 'P3', 'IP0412424', 354642.76, 7402027.05, -23.485384, -46.423415, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412425', 'RUA AVELINO MATOS MACHADO', 'P3', 'IP0412425', 354663.47, 7402014.65, -23.485498, -46.423214, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412426', 'RUA AVELINO MATOS MACHADO', 'P3', 'IP0412426', 354686.89, 7402015.93, -23.485488, -46.422984, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412427', 'RUA AVELINO MATOS MACHADO', 'P3', 'IP0412427', 354713.60, 7402017.88, -23.485473, -46.422723, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412428', 'TRAVESSA SUDAO', 'P3', 'IP0412428', 354690.46, 7402031.41, -23.485349, -46.422948, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0412429', 'TRAVESSA SUDAO', 'P3', 'IP0412429', 354689.82, 7402083.43, -23.484879, -46.422949, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0550388', 'RUA ASCENSO FERNANDES', 'P3', 'IP0550388', 354642.65, 7402008.34, -23.485553, -46.423418, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0598560', 'RUA ANTÔNIO VIANA', 'P3', 'IP0598560', 354616.41, 7402021.30, -23.485434, -46.423674, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0598561', 'RUA VÁRZEA DA PALMA', 'P3', 'IP0598561', 354587.34, 7402020.27, -23.485440, -46.423958, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0676488', 'TRAVESSA Avelino Matos Machado', 'P3', 'IP0676488', 354575.59, 7402014.00, -23.485496, -46.424074, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;
INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n, latitude, longitude, simulado)
VALUES ('JH-IP0714148', 'VIA TV. SUD?O, 56 - JARDIM HELENA, S?O PAULO - SP, 08081-435, BRAZIL', 'P3', 'IP0714148', 354691.15, 7402057.12, -23.485117, -46.422938, true)
ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, simulado = true;

-- Associacao trecho x ponto dos simulados: distancia a linha do trecho <= 25 m (EPSG:31983).
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19319, id, 3.56, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410150'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19319, id, 3.68, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410152'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20802, id, 14.47, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410152'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 14.93, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410152'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 5.46, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410153'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19319, id, 19.18, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410153'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20802, id, 19.94, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410153'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19319, id, 3.43, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410154'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20802, id, 6.41, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410154'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 7.27, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410154'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20802, id, 7.9, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410155'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19319, id, 19.54, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410155'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 19.54, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410155'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 3.58, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410182'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 3.38, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410183'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 2.98, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0410184'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20799, id, 6.06, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411799'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19400, id, 6.68, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411799'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20800, id, 6.68, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411799'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19400, id, 2.34, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411800'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20799, id, 12.56, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411800'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20800, id, 12.77, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0411800'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19400, id, 2.99, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412402'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 19400, id, 3.21, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412403'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20345, id, 6.07, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412414'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 4.09, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412415'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20345, id, 5.8, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412415'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 7.04, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412415'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 2.83, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412416'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20345, id, 14.08, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412416'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 14.32, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412416'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 5.94, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412417'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18571, id, 16.28, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412417'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20345, id, 17.41, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412417'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 22661, id, 5.23, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412419'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18570, id, 6.92, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412419'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 8.63, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412419'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 22.79, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412419'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 22.79, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412419'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18570, id, 4.0, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412420'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 22661, id, 9.99, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412420'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 10.73, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412420'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18570, id, 4.21, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412421'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18570, id, 4.37, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412422'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 22661, id, 5.12, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412423'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 7.25, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412423'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 7.25, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412423'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18570, id, 23.97, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412423'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20121, id, 24.45, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412423'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20799, id, 5.65, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412424'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 9.55, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412424'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 1411, id, 10.82, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412424'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 10.82, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412424'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 4.29, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412425'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 5.0, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412426'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4646, id, 6.53, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412426'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18459, id, 6.53, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412426'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4646, id, 5.3, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412427'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 23.19, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412427'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18459, id, 23.19, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412427'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18459, id, 0.49, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412428'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4646, id, 10.13, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412428'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 10.15, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412428'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18459, id, 3.38, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0412429'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 3.86, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 9.15, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 1411, id, 10.16, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20799, id, 10.16, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20159, id, 19.7, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 22661, id, 19.7, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0550388'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 1411, id, 5.66, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0598560'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 20799, id, 21.11, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0598560'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 4645, id, 21.91, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0598560'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 21198, id, 21.91, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0598560'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 1411, id, 6.95, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0598561'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 1411, id, 1.64, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0676488'
ON CONFLICT DO NOTHING;
INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)
SELECT 18459, id, 2.92, 'distancia a linha do trecho <= 25 m (EPSG:31983)' FROM ponto_de_luz WHERE codigo = 'JH-IP0714148'
ON CONFLICT DO NOTHING;

COMMIT;
