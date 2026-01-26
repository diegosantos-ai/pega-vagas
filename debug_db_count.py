import os

import duckdb

db_path = "data/gold/vagas.duckdb"

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

try:
    con = duckdb.connect(db_path)
    # Check row count
    rows = con.sql("SELECT count(*) FROM fact_vagas").fetchone()[0]
    print(f"📊 Total de linhas na tabela fact_vagas: {rows}")

    if rows > 0:
        print("\n--- Amostra de Dados ---")
        con.sql(
            "SELECT titulo_normalizado, empresa, plataforma, data_coleta FROM fact_vagas LIMIT 5"
        ).show()
    else:
        print("\n⚠️ A tabela está vazia. O problema é na INSERÇÃO do banco.")

except Exception as e:
    print(f"❌ Erro ao ler banco: {e}")
