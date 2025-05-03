import ast
import os

file_path = "geemap_tools/gee_utils.py"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")

with open(file_path, "r", encoding="utf-8") as f:
    tree = ast.parse(f.read(), filename=file_path)

def extract_function_info(node: ast.FunctionDef):
    name = node.name
    args = [arg.arg for arg in node.args.args]
    docstring = ast.get_docstring(node) or "*Sem descrição*"
    return name, args, docstring

# Extrai as funções definidas no arquivo
functions = [
    extract_function_info(node)
    for node in tree.body
    if isinstance(node, ast.FunctionDef)
]

# Gera o manual em Markdown
manual_lines = [
    "# Manual do geemap-tools",
    "",
    "Este manual foi gerado automaticamente a partir das funções presentes em `gee_utils.py`.",
    "",
    "## Funções disponíveis",
    ""
]

for name, args, doc in functions:
    signature = f"### `{name}({', '.join(args)})`"
    manual_lines.append(signature)
    manual_lines.append("")
    manual_lines.append(doc.strip())
    manual_lines.append("")

# Salva
manual_path = "manual.md"
with open(manual_path, "w", encoding="utf-8") as f:
    f.write("\n".join(manual_lines))

print(f"✅ Manual gerado com sucesso: {manual_path}")

