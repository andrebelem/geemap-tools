import re
import os

# Caminho do arquivo Python que contém as funções
file_path = "geemap_tools/gee_utils.py"

# Verifica se o arquivo existe
if not os.path.exists(file_path):
    raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")

# Lê o conteúdo do arquivo
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Expressão regular para encontrar funções com docstring entre aspas simples triplas
pattern = r'def (\w+)\((.*?)\):\s+"""(.*?)"""'
matches = re.findall(pattern, content, re.DOTALL)

# Começa a construir o conteúdo do manual em Markdown
manual_lines = [
    "# Manual do geemap-tools",
    "",
    "Este manual foi gerado automaticamente a partir das funções presentes no módulo `gee_utils.py`.",
    "",
    "## Funções disponíveis",
    ""
]

# Adiciona cada função encontrada ao manual
for name, args, doc in matches:
    manual_lines.append(f"### `{name}({args.strip()})`")
    manual_lines.append("")
    manual_lines.append(doc.strip())
    manual_lines.append("")

# Salva o conteúdo como manual.md na raiz do projeto
manual_path = "manual.md"
with open(manual_path, "w", encoding="utf-8") as f:
    f.write("\n".join(manual_lines))

print(f"✅ Manual gerado em: {manual_path}")
