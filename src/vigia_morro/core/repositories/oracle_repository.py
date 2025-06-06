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
