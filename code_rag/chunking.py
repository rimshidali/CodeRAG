# chunking.py
# Purpose:
# - take (file_path, content) from ingestion
# - produce chunks of text suitable for embedding
# - attach metadata (file, language, symbol, lines, dependencies)
# - use Tree-sitter for code-aware chunking
# - fallback for markdown and plain text
import os 
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Tuple, Any
from tree_sitter import Language, Parser

# -------- 1) configuration --------


# Possible shared library names (Linux, macOS, Windows)
TS_LIB_CANDIDATES = [
    os.path.join("build", "my-languages.so"),     # Linux
    os.path.join("build", "my-languages.dylib"),  # macOS
    os.path.join("build", "my-languages.dll"),    # Windows
]

# Pick whichever exists
TS_LIB_PATH = next((f for f in TS_LIB_CANDIDATES if os.path.exists(f)), None)


# Path to build script
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts", "build_treesitter.py")

# If not found, build it
if TS_LIB_PATH is None:
    print("Tree-sitter library not found. Building...")
    subprocess.check_call(["python3", SCRIPT_DIR])
    # After building, re-scan for the file
    TS_LIB_PATH = next((f for f in TS_LIB_CANDIDATES if os.path.exists(f)), None)

# Final safety check
if TS_LIB_PATH is None:
    raise FileNotFoundError("Failed to build Tree-sitter shared library.")


EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "javascript", ".tsx": "javascript",
    ".java": "java",
    ".c": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp", ".h": "cpp",
    ".go": "go", ".rs": "rust",
    ".md": "markdown", ".markdown": "markdown",
    ".txt": "text",
}

LANG_DEFINITION_NODES = {
    "python": ["function_definition", "class_definition"],
    "javascript": ["function_declaration", "method_definition", "class_declaration"],
    "java": ["method_declaration", "class_declaration"],
    "c": ["function_definition"],
    "cpp": ["function_definition", "class_specifier"],
    "go": ["function_declaration", "method_declaration", "type_declaration"],
    "rust": ["function_item", "impl_item", "struct_item", "enum_item", "trait_item"],
}

# -------- 2) load languages --------
TS_LANGS = {}
for lang in set(EXT_TO_LANG.values()):
    if lang not in ("text", "markdown"):
        TS_LANGS[lang] = Language(TS_LIB_PATH, lang)

# -------- 3) helpers --------
def detect_language(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    return EXT_TO_LANG.get(ext, "text")

def _node_text(content: str, node) -> str:
    return content[node.start_byte:node.end_byte]

def _safe_name_for(language: str, node, content: str) -> str:
    text = _node_text(content, node)
    if language == "python":
        m = re.search(r"^\s*(?:def|class)\s+([A-Za-z_]\w*)", text)
    elif language == "javascript":
        m = re.search(r"^\s*(?:function|class)\s+([A-Za-z_]\w*)", text)
    elif language == "java":
        m = re.search(r"(?:class|interface)\s+([A-Za-z_]\w*)", text)
    elif language in ("c", "cpp"):
        m = re.search(r"\b([A-Za-z_]\w*)\s*\(", text)
    elif language == "go":
        m = re.search(r"^\s*func\s+(?:\([^)]+\)\s+)?([A-Za-z_]\w*)\s*\(", text)
    elif language == "rust":
        m = re.search(r"^\s*(?:fn|struct|enum|trait)\s+([A-Za-z_]\w*)", text)
    else:
        m = None
    return m.group(1) if m else None

def extract_dependencies(language: str, content: str) -> List[str]:
    deps = []
    if language == "python":
        deps += re.findall(r"(?m)^\s*import\s+([a-zA-Z_][\w\.]*)", content)
        deps += re.findall(r"(?m)^\s*from\s+([a-zA-Z_][\w\.]*)\s+import\s+", content)
    elif language == "javascript":
        deps += re.findall(r"(?m)^\s*import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]", content)
        deps += re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
    elif language == "java":
        deps += re.findall(r"(?m)^\s*import\s+([a-zA-Z_][\w\.]*);", content)
    elif language in ("c", "cpp"):
        deps += re.findall(r"(?m)^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]", content)
    elif language == "go":
        deps += re.findall(r"(?s)import\s*(?:\(\s*([\s\S]*?)\s*\)|\"([^\"]+)\")", content)
        norm = []
        for g in deps:
            block, single = g
            if block:
                norm += re.findall(r"\"([^\"]+)\"", block)
            elif single:
                norm.append(single)
        deps = [d for d in norm if d]
    elif language == "rust":
        deps += re.findall(r"(?m)^\s*use\s+([a-zA-Z_][\w:]*)(?:\s*as\s*\w+)?\s*;", content)
    elif language == "markdown":
        deps += re.findall(r"\[.+?\]\(([^)]+)\)", content)
        deps += [f"codeblock:{lang}" for lang in re.findall(r"```(\w+)", content)]
    return sorted(set(deps))

# -------- 4) chunking --------
def chunk_code(file_path: str, content: str, language: str) -> List[Dict[str, Any]]:
    parser = Parser()
    parser.set_language(TS_LANGS[language])
    tree = parser.parse(bytes(content, "utf8"))
    root = tree.root_node

    def_nodes = LANG_DEFINITION_NODES.get(language, [])
    chunks = []

    stack = [root]
    while stack:
        node = stack.pop()
        stack.extend(reversed(node.children))
        if node.type in def_nodes:
            chunks.append({
                "content": _node_text(content, node),
                "metadata": {
                    "file_path": file_path,
                    "language": language,
                    "node_type": node.type,
                    "symbol_name": _safe_name_for(language, node, content),
                    "start_line": node.start_point[0]+1,
                    "end_line": node.end_point[0]+1,
                }
            })

    if not chunks:
        chunks.append({
            "content": content,
            "metadata": {
                "file_path": file_path,
                "language": language,
                "node_type": "file",
                "symbol_name": Path(file_path).name,
                "start_line": 1,
                "end_line": len(content.splitlines()) or 1,
            }
        })
    return chunks

def chunk_markdown(file_path: str, content: str) -> List[Dict[str, Any]]:
    parts = re.split(r"(?m)(^#{1,6}\s+.*$)", content)
    sections = []
    for i in range(0, len(parts), 2):
        heading = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        block = (heading + body).strip()
        if block:
            sections.append(block)

    chunks = []
    section_id = 0
    MAX_WORDS = 400
    for sec in sections or [content]:
        words = sec.split()
        if len(words) <= MAX_WORDS:
            chunks.append({
                "content": sec,
                "metadata": {"file_path": file_path, "language": "markdown",
                             "node_type": "section", "symbol_name": None,
                             "section_id": section_id}
            })
            section_id += 1
        else:
            paras = [p.strip() for p in sec.split("\n\n") if p.strip()]
            buf = []
            for para in paras:
                if len(" ".join(buf + [para]).split()) <= MAX_WORDS:
                    buf.append(para)
                else:
                    chunks.append({
                        "content": "\n\n".join(buf),
                        "metadata": {"file_path": file_path, "language": "markdown",
                                     "node_type": "section", "symbol_name": None,
                                     "section_id": section_id}
                    })
                    section_id += 1
                    buf = [para]
            if buf:
                chunks.append({
                    "content": "\n\n".join(buf),
                    "metadata": {"file_path": file_path, "language": "markdown",
                                 "node_type": "section", "symbol_name": None,
                                 "section_id": section_id}
                })
                section_id += 1
    return chunks

def chunk_text(file_path: str, content: str) -> List[Dict[str, Any]]:
    LINES_PER_CHUNK = 80
    lines = content.splitlines()
    chunks = []
    for i in range(0, len(lines), LINES_PER_CHUNK):
        part = "\n".join(lines[i:i+LINES_PER_CHUNK]).strip()
        if part:
            chunks.append({
                "content": part,
                "metadata": {"file_path": file_path, "language": "text",
                             "node_type": "block", "symbol_name": None,
                             "block_id": i // LINES_PER_CHUNK}
            })
    if not chunks and content.strip():
        chunks.append({
            "content": content.strip(),
            "metadata": {"file_path": file_path, "language": "text",
                         "node_type": "block", "symbol_name": None,
                         "block_id": 0}
        })
    return chunks

# -------- 5) public API --------
def chunk_file(file_path: str, content: str) -> List[Dict[str, Any]]:
    language = detect_language(file_path)
    deps = extract_dependencies(language, content)

    if language == "markdown":
        chunks = chunk_markdown(file_path, content)
    elif language != "text":
        chunks = chunk_code(file_path, content, language)
    else:
        chunks = chunk_text(file_path, content)

    # add dependencies and chunk_id
    for idx, ch in enumerate(chunks):
        ch["metadata"]["dependencies"] = deps
        ch["metadata"]["chunk_id"] = f"{file_path}::chunk{idx}"
    return chunks

def chunk_codebase(files: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    all_chunks = []
    for file_path, content in files:
        try:
            all_chunks.extend(chunk_file(file_path, content))
        except Exception as e:
            all_chunks.append({
                "content": content[:2000],
                "metadata": {"file_path": file_path, "language": "text",
                             "node_type": "error_fallback", "symbol_name": None,
                             "chunk_id": f"{file_path}::error0",
                             "dependencies": [], "error": str(e)}
            })
    return all_chunks


