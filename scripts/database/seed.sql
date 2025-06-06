-- Inserir morros
INSERT INTO morros (morro_id, nome, latitude, longitude) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Morro da Serra', -23.5505, -46.6333);

-- Inserir métricas
INSERT INTO tipo_metricas (tipo_metrica_id, nome, unidade) VALUES ('550e8400-e29b-41d4-a716-446655440010', 'Umidade', '%');
INSERT INTO tipo_metricas (tipo_metrica_id, nome, unidade) VALUES ('550e8400-e29b-41d4-a716-446655440011', 'Temperatura', '°C');

INSERT INTO versoes_caixa (versao_id, nome, tipo_caixa) VALUES ('550e8400-e29b-41d4-a716-446655440001', 'Sensor Versão 1', 'sensor');
INSERT INTO versao_metricas (versao_id, tipo_metrica_id) VALUES ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440010');
INSERT INTO versao_metricas (versao_id, tipo_metrica_id) VALUES ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440011');


-- Inserir caixas
INSERT INTO caixas (caixa_id, tipo, versao_id, morro_id, latitude, longitude, ativo, codigo_patrimonio) 
VALUES ('550e8400-e29b-41d4-a716-446655440003', 'sensor', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', -23.5505, -46.6333, 1, 'CAIXA001');
INSERT INTO caixas (caixa_id, tipo, versao_id, morro_id, latitude, longitude, ativo, codigo_patrimonio) 
VALUES ('550e8400-e29b-41d4-a716-446655440004', 'sensor', '550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440000', -22.9068, -43.1729, 1, 'CAIXA002');


INSERT INTO versoes_caixa (versao_id, nome, tipo_caixa) VALUES ('550e8400-e29b-41d4-a716-446655410001', 'Alerta Versao 1', 'alerta');
INSERT INTO caixas (caixa_id, tipo, versao_id, morro_id, latitude, longitude, ativo, codigo_patrimonio) 
VALUES ('550e8400-e29b-41d4-a716-446655440005', 'alerta', '550e8400-e29b-41d4-a716-446655410001', '550e8400-e29b-41d4-a716-446655440000', -23.5505, -46.6333, 1, 'ALERTA001');