import os
import oracledb

class OracleRepository:
    def __init__(self):
        user = os.getenv("ORACLE_USER")
        password = os.getenv("ORACLE_PASSWORD")
        dsn = os.getenv("ORACLE_DSN")
        self.conn = oracledb.connect(user=user, password=password, dsn=dsn)

    # Morro
    def morro_existe(self, morro_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM morros WHERE morro_id = :1", [morro_id])
        result = cursor.fetchone()[0]
        cursor.close()
        return result > 0

    def inserir_morro(self, morro_id, nome, coordenadas):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO morros (morro_id, nome, latitude, longitude)
            VALUES (:1, :2, :3, :4)
        """, (morro_id, nome, coordenadas[0], coordenadas[1]))
        self.conn.commit()
        cursor.close()

    def listar_morros(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT morro_id, nome, latitude, longitude FROM morros")
        morros = []
        for row in cursor.fetchall():
            morros.append({
                "morro_id": row[0],
                "nome": row[1],
                "coordenadas": [row[2], row[3]]
            })
        cursor.close()
        return morros

    def remover_morro(self, morro_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM morros WHERE morro_id = :1", [morro_id])
            self.conn.commit()
        except oracledb.IntegrityError as e:
            if "FK_MORRO" in str(e):
                raise ValueError(f"Não é possível remover o morro '{morro_id}' porque ele está vinculado a caixas.")
            else:
                raise
        finally:
            cursor.close()

    # Caixa
    def caixa_existe(self, caixa_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM caixas WHERE caixa_id = :1", [caixa_id])
        result = cursor.fetchone()[0]
        cursor.close()
        return result > 0

    def caixa_codigo_existe(self, codigo_patrimonio):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM caixas WHERE codigo_patrimonio = :1", [codigo_patrimonio])
        result = cursor.fetchone()[0]
        cursor.close()
        return result > 0

    def inserir_caixa(self, caixa_id, tipo, versao_id, morro_id, coordenadas, codigo_patrimonio):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO caixas (caixa_id, tipo, versao_id, morro_id, latitude, longitude, ativo, codigo_patrimonio)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        """, (caixa_id, tipo, versao_id, morro_id, coordenadas[0], coordenadas[1], 1, codigo_patrimonio))
        self.conn.commit()
        cursor.close()

    def listar_caixas(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.caixa_id, c.codigo_patrimonio, c.tipo, m.morro_id, m.nome AS morro_nome, 
                   c.latitude, c.longitude, c.ativo,
                   LISTAGG(tm.nome, ', ') WITHIN GROUP (ORDER BY tm.nome) AS sensores
            FROM caixas c
            JOIN morros m ON c.morro_id = m.morro_id
            LEFT JOIN versao_metricas vm ON c.versao_id = vm.versao_id
            LEFT JOIN tipo_metricas tm ON vm.tipo_metrica_id = tm.tipo_metrica_id
            GROUP BY c.caixa_id, c.codigo_patrimonio, c.tipo, m.morro_id, m.nome, 
                     c.latitude, c.longitude, c.ativo
        """)
        caixas = []
        for row in cursor.fetchall():
            caixas.append({
                "caixa_id": row[0],
                "codigo_patrimonio": row[1],
                "tipo": row[2],
                "morro_id": row[3],
                "morro_nome": row[4],
                "coordenadas": [row[5], row[6]],
                "ativo": bool(row[7]),
                "sensores": row[8] or "Nenhum"
            })
        cursor.close()
        return caixas

    def remover_caixa(self, caixa_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM caixas WHERE caixa_id = :1", [caixa_id])
            self.conn.commit()
        except oracledb.IntegrityError as e:
            if "FK_CAIXA" in str(e):
                raise ValueError(f"Não é possível remover a caixa '{caixa_id}' porque ela está vinculada a leituras.")
            else:
                raise
        finally:
            cursor.close()

    # Leituras
    def listar_leituras_por_morro(self, morro_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.morro_id, m.nome AS nome_morro, c.caixa_id, c.codigo_patrimonio AS nome_caixa, 
                   tm.nome AS tipo_metrica, l.valor, l.timestamp
            FROM leituras l
            JOIN caixas c ON l.caixa_id = c.caixa_id
            JOIN morros m ON c.morro_id = m.morro_id
            JOIN tipo_metricas tm ON l.tipo_metrica_id = tm.tipo_metrica_id
            WHERE m.morro_id = :1
        """, [morro_id])
        leituras = [
            {
                "morro_id": row[0],
                "nome_morro": row[1],
                "caixa_id": row[2],
                "nome_caixa": row[3],
                "tipo_metrica": row[4],
                "valor": row[5],
                "timestamp": row[6]
            }
            for row in cursor.fetchall()
        ]
        cursor.close()
        return leituras

    def salvar_leitura(self, leitura: dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO leituras (caixa_id, tipo_metrica_id, valor, timestamp)
            VALUES (:1, :2, :3, :4)
        """, (
            leitura["caixa_id"],
            leitura["tipo_metrica_id"],
            leitura["valor"],
            leitura["timestamp"],
        ))
        self.conn.commit()
        cursor.close()

    def caixa_existe_no_morro(self, codigo_patrimonio, morro_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM caixas
            WHERE codigo_patrimonio = :1 AND morro_id = :2
        """, [codigo_patrimonio, morro_id])
        result = cursor.fetchone()[0]
        cursor.close()
        return result > 0

    def get_versao_id_by_nome(self, nome):
        cursor = self.conn.cursor()
        cursor.execute("SELECT versao_id FROM versoes_caixa WHERE nome = :1", [nome])
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_tipo_metrica_id_by_nome(self, nome_metrica):
        cursor = self.conn.cursor()
        cursor.execute("SELECT tipo_metrica_id FROM tipo_metricas WHERE nome = :1", [nome_metrica])
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def get_caixa_id_by_codigo(self, codigo_patrimonio):
        cursor = self.conn.cursor()
        cursor.execute("SELECT caixa_id FROM caixas WHERE codigo_patrimonio = :1", [codigo_patrimonio])
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def listar_alertas_ativos(self, morro_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT alerta_id, morro_id, caixa_id, status, data_inicio, data_final
            FROM alerta
            WHERE morro_id = :1 AND data_final IS NULL
        """, [morro_id])
        alertas = [
            {
                "alerta_id": row[0],
                "morro_id": row[1],
                "caixa_id": row[2],
                "status": row[3],
                "data_inicio": row[4],
                "data_final": row[5]
            }
            for row in cursor.fetchall()
        ]
        cursor.close()
        return alertas

    def salvar_dados_meteorologicos(self, morro_id, temperatura, umidade, descricao, chovendo):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO meteorologia (morro_id, temperatura, umidade, descricao, chovendo)
            VALUES (:1, :2, :3, :4, :5)
        """, (morro_id, temperatura, umidade, descricao, chovendo))
        self.conn.commit()
        cursor.close()

    def listar_caixas_alerta_por_morro(self, morro_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT caixa_id
            FROM caixas
            WHERE morro_id = :1 AND tipo = 'alerta'
        """, [morro_id])
        caixas = [{"caixa_id": row[0]} for row in cursor.fetchall()]
        cursor.close()
        return caixas

    def alerta_ativo_para_caixa(self, caixa_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM alerta
            WHERE caixa_id = :1 AND data_final IS NULL
        """, [caixa_id])
        result = cursor.fetchone()[0]
        cursor.close()
        return result > 0

    def registrar_alerta(self, morro_id, caixa_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alerta (morro_id, caixa_id, status, data_inicio)
            VALUES (:1, :2, 'Ativo', CURRENT_TIMESTAMP)
        """, [morro_id, caixa_id])
        self.conn.commit()
        cursor.close()

    def desligar_alerta(self, alerta_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE alerta
            SET data_final = CURRENT_TIMESTAMP, status = 'Inativo'
            WHERE alerta_id = :1
        """, [alerta_id])
        self.conn.commit()
        cursor.close()

    def obter_leituras_solo_para_treino(self, resolucao_minutos=10):
        """
        Retorna a umidade do solo média, máxima e mínima agrupada pelo tipo de métrica
        para um determinado morro, com resolução configurável em minutos.
        Inclui um campo de datetime formatado com a resolução.
        """
        query = f"""
        SELECT
            TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE AS intervalo_tempo,
            TO_CHAR(TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, 'YYYY-MM-DD HH24:MI:SS') AS datetime_formatado,
            tm.nome AS tipo_metrica,
            AVG(l.valor) AS metrica_media,
            MAX(l.valor) AS metrica_maxima,
            MIN(l.valor) AS metrica_minima,
            c.morro_id
        FROM leituras l
        JOIN caixas c ON l.caixa_id = c.caixa_id
        JOIN tipo_metricas tm ON l.tipo_metrica_id = tm.tipo_metrica_id
        GROUP BY TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, tm.nome, c.morro_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return [
            {
                "intervalo_tempo": row[0],  # Objeto de intervalo de tempo
                "datetime_formatado": row[1],  # Campo formatado como string
                "tipo_metrica": row[2].lower(),
                "media": row[3],
                "maxima": row[4],
                "minima": row[5],
                "morro_id": row[6]
            }
            for row in results
        ]

    def obter_meteorologia_para_treino(self, resolucao_minutos=10):
        """
        Retorna os dados de meteorologia (temperatura, umidade e estado de chuva) agrupados
        por intervalos configuráveis em minutos para um determinado morro.
        Inclui um campo de datetime formatado com a resolução.
        """
        query = f"""
        SELECT
            TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE AS intervalo_tempo,
            TO_CHAR(TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, 'YYYY-MM-DD HH24:MI:SS') AS datetime_formatado,
            AVG(m.temperatura) AS temperatura_media,
            AVG(m.umidade) AS umidade_media,
            MAX(m.chovendo) AS chovendo, -- Se chover em qualquer ponto do intervalo, considera como chovendo
            m.morro_id
        FROM meteorologia m
        GROUP BY TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, m.morro_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        return [
            {
                "intervalo_tempo": row[0],  # Objeto de intervalo de tempo
                "datetime_formatado": row[1],  # Campo formatado como string
                "temperatura_media": row[2],
                "umidade_media": row[3],
                "chovendo": bool(row[4]),   # Converte para booleano (1 = True, 0 = False)
                "morro_id": row[5]
            }
            for row in results
        ]

    def obter_leituras_solo_por_morro(self, morro_id, resolucao_minutos=10):
        """
        Retorna a umidade do solo média, máxima e mínima agrupada pelo tipo de métrica
        para um determinado morro, com resolução configurável em minutos.
        Inclui um campo de datetime formatado com a resolução e limitado aos últimos 3 dias.
        """
        query = f"""
        SELECT
            TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE AS intervalo_tempo,
            TO_CHAR(TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, 'YYYY-MM-DD HH24:MI:SS') AS datetime_formatado,
            tm.nome AS tipo_metrica,
            AVG(l.valor) AS metrica_media,
            MAX(l.valor) AS metrica_maxima,
            MIN(l.valor) AS metrica_minima,
            c.morro_id
        FROM leituras l
        JOIN caixas c ON l.caixa_id = c.caixa_id
        JOIN tipo_metricas tm ON l.tipo_metrica_id = tm.tipo_metrica_id
        WHERE c.morro_id = :morro_id
          AND l.timestamp >= SYSDATE - INTERVAL '3' MINUTE
        GROUP BY TRUNC(l.timestamp, 'MI') + FLOOR(EXTRACT(MINUTE FROM l.timestamp) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, tm.nome, c.morro_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query, {"morro_id": morro_id})
        results = cursor.fetchall()
        cursor.close()

        return [
            {
                "intervalo_tempo": row[0],  # Objeto de intervalo de tempo
                "datetime_formatado": row[1],  # Campo formatado como string
                "tipo_metrica": row[2].lower(),
                "media": row[3],
                "maxima": row[4],
                "minima": row[5],
                "morro_id": row[6]
            }
            for row in results
        ]

    def obter_meteorologia_por_morro(self, morro_id, resolucao_minutos=10):
        """
        Retorna os dados de meteorologia (temperatura, umidade e estado de chuva) agrupados
        por intervalos configuráveis em minutos para um determinado morro.
        Inclui um campo de datetime formatado com a resolução e limitado aos últimos 3 dias.
        """
        query = f"""
        SELECT
            TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE AS intervalo_tempo,
            TO_CHAR(TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, 'YYYY-MM-DD HH24:MI:SS') AS datetime_formatado,
            AVG(m.temperatura) AS temperatura_media,
            AVG(m.umidade) AS umidade_media,
            MAX(m.chovendo) AS chovendo, -- Se chover em qualquer ponto do intervalo, considera como chovendo
            m.morro_id
        FROM meteorologia m
        WHERE m.morro_id = :morro_id
          AND m.data_hora >= SYSDATE - INTERVAL '3' MINUTE
        GROUP BY TRUNC(m.data_hora, 'MI') + FLOOR(EXTRACT(MINUTE FROM m.data_hora) / {resolucao_minutos}) * INTERVAL '{resolucao_minutos}' MINUTE, m.morro_id
        """
        cursor = self.conn.cursor()
        cursor.execute(query, {"morro_id": morro_id})
        results = cursor.fetchall()
        cursor.close()

        return [
            {
                "intervalo_tempo": row[0],  # Objeto de intervalo de tempo
                "datetime_formatado": row[1],  # Campo formatado como string
                "temperatura_media": row[2],
                "umidade_media": row[3],
                "chovendo": bool(row[4]),   # Converte para booleano (1 = True, 0 = False)
                "morro_id": row[5]
            }
            for row in results
        ]
