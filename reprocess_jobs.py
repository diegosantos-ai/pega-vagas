"""
Script para reprocessar vagas existentes com os novos normalizers.

Aplica:
1. Normalização de títulos melhorada
2. Inferência de senioridade
3. Extração e normalização de localidades
4. Adição do setor da empresa

Uso:
    python reprocess_jobs.py
    python reprocess_jobs.py --dry-run  # Preview sem salvar
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import structlog

from src.processing.normalizers import (
    normalize_job_title,
    normalize_seniority,
    normalize_location,
    parse_location_string,
    extract_location_from_text,
)
from src.config.companies import get_all_companies, get_sector_for_company, SECTOR_BY_CATEGORY


logger = structlog.get_logger()


# Mapeamento empresa -> setor (baseado em companies.py)
COMPANY_SECTOR_MAP = {}
for company in get_all_companies():
    COMPANY_SECTOR_MAP[company.name.lower()] = get_sector_for_company(company)


def get_sector_by_company_name(company_name: str) -> Optional[str]:
    """Retorna o setor baseado no nome da empresa."""
    if not company_name:
        return None
    
    name_lower = company_name.lower().strip()
    
    # Match exato
    if name_lower in COMPANY_SECTOR_MAP:
        return COMPANY_SECTOR_MAP[name_lower]
    
    # Match parcial
    for key, sector in COMPANY_SECTOR_MAP.items():
        if key in name_lower or name_lower in key:
            return sector
            
    return None


def reprocess_job(job_data: dict, file_path: Path) -> dict:
    """
    Reprocessa uma vaga aplicando os novos normalizers.
    
    Args:
        job_data: Dados originais da vaga
        file_path: Caminho do arquivo (para logging)
        
    Returns:
        Dados atualizados da vaga
    """
    vaga = job_data.get("vaga", {})
    
    titulo_original = vaga.get("titulo_original", "")
    titulo_atual = vaga.get("titulo_normalizado", "")
    empresa = vaga.get("empresa", "")
    
    # 1. Renormaliza título
    novo_titulo = normalize_job_title(titulo_original)
    if titulo_atual == "Outro" and novo_titulo != "Outro":
        logger.info(
            "Titulo corrigido",
            original=titulo_original[:50],
            de=titulo_atual,
            para=novo_titulo
        )
    
    # 2. Renormaliza senioridade
    senioridade_atual = vaga.get("senioridade", "")
    nova_senioridade = normalize_seniority(titulo_original)
    if nova_senioridade and nova_senioridade != senioridade_atual:
        logger.debug(
            "Senioridade atualizada",
            original=titulo_original[:40],
            de=senioridade_atual,
            para=nova_senioridade
        )
    
    # 3. Tenta extrair/normalizar localidade
    localidade_atual = vaga.get("localidade")
    nova_localidade = localidade_atual
    
    # Se não tem localidade, tenta extrair do título ou descrição
    if not localidade_atual:
        descricao = vaga.get("descricao_resumida", "")
        texto_busca = f"{titulo_original} {descricao}"
        loc_info = extract_location_from_text(texto_busca)
        if loc_info.get("cidade") or loc_info.get("estado"):
            # Formata como "Cidade, UF" ou apenas "UF"
            if loc_info.get("cidade") and loc_info.get("estado"):
                nova_localidade = f"{loc_info['cidade']}, {loc_info['estado']}"
            elif loc_info.get("estado"):
                nova_localidade = loc_info['estado']
            elif loc_info.get("is_remote"):
                nova_localidade = "Remoto"
            logger.debug(
                "Localidade extraida",
                original=texto_busca[:50],
                localidade=nova_localidade
            )
    elif localidade_atual:
        # Normaliza localidade existente (se for string)
        if isinstance(localidade_atual, str):
            loc_info = parse_location_string(localidade_atual)
            if loc_info.get("cidade") and loc_info.get("estado"):
                nova_localidade = f"{loc_info['cidade']}, {loc_info['estado']}"
            elif loc_info.get("estado"):
                nova_localidade = loc_info['estado']
            elif loc_info.get("is_remote"):
                nova_localidade = "Remoto"
            if nova_localidade != localidade_atual:
                logger.debug(
                    "Localidade normalizada",
                    de=localidade_atual,
                    para=nova_localidade
                )
    
    # 4. Adiciona setor da empresa se não existir
    setor_atual = vaga.get("setor_empresa")
    novo_setor = setor_atual
    if not setor_atual and empresa:
        novo_setor = get_sector_by_company_name(empresa)
        if novo_setor:
            logger.debug("Setor adicionado", empresa=empresa, setor=novo_setor)
    
    # Atualiza vaga
    vaga_atualizada = vaga.copy()
    vaga_atualizada["titulo_normalizado"] = novo_titulo
    vaga_atualizada["senioridade"] = nova_senioridade or senioridade_atual
    vaga_atualizada["localidade"] = nova_localidade
    vaga_atualizada["setor_empresa"] = novo_setor
    
    # Marca como reprocessado
    job_data_atualizado = job_data.copy()
    job_data_atualizado["vaga"] = vaga_atualizada
    job_data_atualizado["_reprocessado_em"] = datetime.now().isoformat()
    
    return job_data_atualizado


def analyze_before_after(jobs: list[dict]) -> dict:
    """Analisa estatísticas antes e depois do reprocessamento."""
    stats = {
        "total": len(jobs),
        "titulos_outro_antes": 0,
        "titulos_outro_depois": 0,
        "sem_localidade_antes": 0,
        "sem_localidade_depois": 0,
        "sem_setor_antes": 0,
        "sem_setor_depois": 0,
        "titulos_corrigidos": 0,
        "localidades_adicionadas": 0,
        "setores_adicionados": 0,
    }
    
    for job in jobs:
        vaga_antes = job.get("vaga_original", {})
        vaga_depois = job.get("vaga", {})
        
        # Títulos
        if vaga_antes.get("titulo_normalizado") == "Outro":
            stats["titulos_outro_antes"] += 1
        if vaga_depois.get("titulo_normalizado") == "Outro":
            stats["titulos_outro_depois"] += 1
        if vaga_antes.get("titulo_normalizado") == "Outro" and vaga_depois.get("titulo_normalizado") != "Outro":
            stats["titulos_corrigidos"] += 1
            
        # Localidades
        if not vaga_antes.get("localidade"):
            stats["sem_localidade_antes"] += 1
        if not vaga_depois.get("localidade"):
            stats["sem_localidade_depois"] += 1
        if not vaga_antes.get("localidade") and vaga_depois.get("localidade"):
            stats["localidades_adicionadas"] += 1
            
        # Setores
        if not vaga_antes.get("setor_empresa"):
            stats["sem_setor_antes"] += 1
        if not vaga_depois.get("setor_empresa"):
            stats["sem_setor_depois"] += 1
        if not vaga_antes.get("setor_empresa") and vaga_depois.get("setor_empresa"):
            stats["setores_adicionados"] += 1
            
    return stats


def main():
    parser = argparse.ArgumentParser(description="Reprocessa vagas com normalizers atualizados")
    parser.add_argument("--dry-run", action="store_true", help="Preview sem salvar alteracoes")
    parser.add_argument("--silver-dir", default="data/silver", help="Diretorio de vagas silver")
    args = parser.parse_args()
    
    silver_dir = Path(args.silver_dir)
    
    if not silver_dir.exists():
        print(f"Erro: Diretorio {silver_dir} nao existe")
        return
    
    # Lista arquivos JSON
    json_files = list(silver_dir.glob("*_processed.json"))
    print(f"\nEncontrados {len(json_files)} arquivos para reprocessar\n")
    
    if not json_files:
        print("Nenhum arquivo para processar")
        return
    
    jobs_reprocessados = []
    erros = 0
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                job_data = json.load(f)
            
            # Guarda original para comparacao
            vaga_original = job_data.get("vaga", {}).copy()
            
            # Reprocessa
            job_atualizado = reprocess_job(job_data, file_path)
            job_atualizado["vaga_original"] = vaga_original
            
            jobs_reprocessados.append(job_atualizado)
            
            # Salva se não for dry-run
            if not args.dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    # Remove vaga_original antes de salvar
                    job_para_salvar = job_atualizado.copy()
                    del job_para_salvar["vaga_original"]
                    json.dump(job_para_salvar, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            print(f"Erro ao processar {file_path.name}: {e}")
            erros += 1
    
    # Estatísticas
    stats = analyze_before_after(jobs_reprocessados)
    
    print("=" * 60)
    print("ESTATISTICAS DE REPROCESSAMENTO")
    print("=" * 60)
    print(f"Total de vagas: {stats['total']}")
    print()
    print("TITULOS:")
    print(f"  'Outro' antes:  {stats['titulos_outro_antes']} ({100*stats['titulos_outro_antes']/stats['total']:.1f}%)")
    print(f"  'Outro' depois: {stats['titulos_outro_depois']} ({100*stats['titulos_outro_depois']/stats['total']:.1f}%)")
    print(f"  Corrigidos:     {stats['titulos_corrigidos']}")
    print()
    print("LOCALIDADES:")
    print(f"  Vazias antes:  {stats['sem_localidade_antes']}")
    print(f"  Vazias depois: {stats['sem_localidade_depois']}")
    print(f"  Adicionadas:   {stats['localidades_adicionadas']}")
    print()
    print("SETORES:")
    print(f"  Vazios antes:  {stats['sem_setor_antes']}")
    print(f"  Vazios depois: {stats['sem_setor_depois']}")
    print(f"  Adicionados:   {stats['setores_adicionados']}")
    print()
    
    if args.dry_run:
        print("[DRY-RUN] Nenhuma alteracao foi salva")
    else:
        print(f"Arquivos atualizados: {len(jobs_reprocessados) - erros}")
    
    if erros:
        print(f"Erros: {erros}")


if __name__ == "__main__":
    main()
