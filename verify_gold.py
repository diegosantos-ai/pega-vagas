import duckdb

try:
    con = duckdb.connect("data/gold/vagas.duckdb")
    print("--- DADOS POR PLATAFORMA ---")
    # Corrected column name to 'plataforma'
    con.sql("SELECT plataforma, count(1) as total FROM fact_vagas GROUP BY plataforma").show()

    print("\n--- AMOSTRA LINKEDIN ---")
    # Corrected column name to 'plataforma' and added 'modelo_trabalho' check
    con.sql(
        "SELECT titulo_normalizado, empresa, modelo_trabalho FROM fact_vagas WHERE plataforma = 'linkedin' LIMIT 5"
    ).show()
except Exception as e:
    print(f"Erro: {e}")
