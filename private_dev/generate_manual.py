"""
generate_manual.py

Script de uso interno para gerar automaticamente a documentação de uso do pacote `geemap-tools`
a partir das docstrings das funções públicas.

Este script busca todas as funções com docstrings bilíngues nos módulos do pacote,
e cria um arquivo `USAGE.md` com estrutura em Markdown legível.

Uso:
    python private_dev/generate_manual.py

Este script é destinado apenas para fins de manutenção e documentação do projeto.
Ele **não é incluído na instalação via pip**.
"""

import re
import sys
from pathlib import Path

# Garante que estamos sempre partindo da raiz do repositório
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "geemap_tools"
OUTPUT_FILE = REPO_ROOT / "USAGE.md"

# Cabeçalho do arquivo gerado
header = """# USAGE

This document was generated automatically from the public functions defined in `geemap_tools`.

Each function is documented using bilingual docstrings (Portuguese and English) and grouped by module.

---

"""

def extract_docstrings(file_path):
    """
    Extrai docstrings de funções públicas com aspas triplas em um arquivo Python.
    Retorna uma lista de tuplas: (nome, argumentos, docstring limpa).
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Expressão regular para encontrar funções com docstrings entre aspas triplas
    pattern = r"def (\w+)\((.*?)\):\s+\"\"\"(.*?)\"\"\""
    matches = re.findall(pattern, content, re.DOTALL)

    docs = []
    for name, args, doc in matches:
        if name.startswith("_"):
            continue  # ignora funções privadas
        clean_doc = "\n".join(line.strip() for line in doc.strip().splitlines())
        docs.append((name, args, clean_doc))

    return docs

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(header)

        for pyfile in sorted(MODULE_DIR.glob("*.py")):
            if pyfile.name.startswith("_") or pyfile.name.startswith("dev"):
                continue

            module_name = pyfile.stem
            f.write(f"\n## Module `{module_name}`\n")

            functions = extract_docstrings(pyfile)
            if not functions:
                f.write("\n*(no public functions found)*\n")
                continue

            for name, args, doc in functions:
                f.write(f"\n### `{name}({args})`\n\n")
                f.write(f"{doc}\n")

    print(f"✅ USAGE.md successfully generated at: {OUTPUT_FILE}")
    print(f"📄 File size: {OUTPUT_FILE.stat().st_size} bytes")

if __name__ == "__main__":
    main()