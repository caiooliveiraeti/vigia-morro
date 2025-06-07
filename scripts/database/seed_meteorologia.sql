DECLARE
    v_start_date DATE := SYSDATE - 50; -- Começa 50 dias atrás
    v_end_date DATE := SYSDATE; -- Até a data atual
    v_current_date DATE;
    v_minute_interval NUMBER := 10; -- Intervalo de 10 minutos
    v_chovendo NUMBER;
BEGIN
    v_current_date := v_start_date;

    WHILE v_current_date <= v_end_date LOOP
        FOR v_minute IN 0 .. (24 * 60 / v_minute_interval) - 1 LOOP
            -- Determinar se está chovendo
            v_chovendo := CASE
                WHEN DBMS_RANDOM.VALUE(0, 1) > 0.5 THEN 1 ELSE 0
            END;

            -- Inserir os dados meteorológicos
            INSERT INTO meteorologia (morro_id, temperatura, umidade, descricao, chovendo, data_hora)
            VALUES (
                '550e8400-e29b-41d4-a716-446655440000', -- ID do Morro da Serra
                ROUND(DBMS_RANDOM.VALUE(15, 35), 1), -- Temperatura entre 15°C e 35°C
                ROUND(DBMS_RANDOM.VALUE(40, 90), 1), -- Umidade entre 40% e 90%
                CASE
                    WHEN v_chovendo = 1 AND DBMS_RANDOM.VALUE(0, 1) > 0.8 THEN 'chuva forte' -- 20% de chance de chuva forte
                    WHEN v_chovendo = 1 THEN 'chuva moderada' -- Caso esteja chovendo, mas não seja forte
                    ELSE 'céu limpo' -- Caso não esteja chovendo
                END,
                v_chovendo, -- Alinha o estado de chuva
                v_current_date + (v_minute * v_minute_interval / (24 * 60)) -- Incrementa o tempo em 10 minutos
            );

            -- Inserir leituras de temperatura
            INSERT INTO leituras (caixa_id, tipo_metrica_id, valor, timestamp)
            VALUES (
                '550e8400-e29b-41d4-a716-446655440003', -- ID do sensor de temperatura
                '550e8400-e29b-41d4-a716-446655440011', -- ID da métrica de temperatura
                ROUND(DBMS_RANDOM.VALUE(15, 35), 1), -- Temperatura entre 15°C e 35°C
                v_current_date + (v_minute * v_minute_interval / (24 * 60)) -- Incrementa o tempo em 10 minutos
            );

            -- Inserir leituras de umidade
            INSERT INTO leituras (caixa_id, tipo_metrica_id, valor, timestamp)
            VALUES (
                '550e8400-e29b-41d4-a716-446655440004', -- ID do sensor de umidade
                '550e8400-e29b-41d4-a716-446655440010', -- ID da métrica de umidade
                ROUND(DBMS_RANDOM.VALUE(40, 90), 1), -- Umidade entre 40% e 90%
                v_current_date + (v_minute * v_minute_interval / (24 * 60)) -- Incrementa o tempo em 10 minutos
            );
        END LOOP;

        v_current_date := v_current_date + 1; -- Incrementa o dia
    END LOOP;

    COMMIT;
END;