import ast
import os

# Caminho base do pacote
base_dir = "geemap_tools"
manual_path = "manual.md"

# Ignorar arquivos especiais
excluded_files = {"__init__.py", "__pycache__"}

def extract_function_info(node: ast.FunctionDef):
    name = node.name
    args = [arg.arg for arg in node.args.args]
    docstring = ast.get_docstring(node) or "*Sem descrição*"
    return name, args, docstring

manual_lines = [
    "# 📘 Manual do geemap-tools",
    "",
    "Este manual foi gerado automaticamente a partir das funções públicas presentes nos submódulos de `geemap_tools`.",
    ""
]

# Percorre todos os arquivos .py na pasta geemap_tools
for filename in sorted(os.listdir(base_dir)):
    if not filename.endswith(".py") or filename in excluded_files:
        continue

    file_path = os.path.join(base_dir, filename)
    module_name = filename.replace(".py", "")
    
    manual_lines.append(f"## 📂 Módulo `{module_name}`")
    manual_lines.append("")

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except SyntaxError as e:
            manual_lines.append(f"⚠️ Erro ao analisar `{filename}`: {e}")
            manual_lines.append("")
            continue

    functions = [
        extract_function_info(node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]

    if not functions:
        manual_lines.append("_Nenhuma função pública encontrada._")
        manual_lines.append("")
        continue

    for name, args, doc in functions:
        signature = f"### `{name}({', '.join(args)})`"
        manual_lines.append(signature)
        manual_lines.append("")
        manual_lines.append(doc.strip())
        manual_lines.append("")

# Salva o manual
with open(manual_path, "w", encoding="utf-8") as f:
    f.write("\n".join(manual_lines))

print(f"✅ Manual gerado com sucesso: {manual_path}")