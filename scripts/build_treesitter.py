import os
import shutil
import sys
from tree_sitter import Language

# Check Git installation before doing anything, otherwise git clone will throw error 
if shutil.which("git") is None:
    sys.exit("Error: Git is not installed or not in PATH. Please install Git first.")

# Folder to store build outputs
BUILD_DIR = "build"
LIB_NAME = "my-languages"

# Detect correct extension based on OS
if os.name == "nt":  # Windows
    LIB_FILE = f"{LIB_NAME}.dll"
elif os.uname().sysname == "Darwin":  # macOS
    LIB_FILE = f"{LIB_NAME}.dylib"
else:  # Linux and others
    LIB_FILE = f"{LIB_NAME}.so"

TS_LIB_PATH = os.path.join(BUILD_DIR, LIB_FILE)

# Grammars to include (you can add/remove as needed)
GRAMMARS = [
    "vendor/tree-sitter-python",
    "vendor/tree-sitter-javascript",
    "vendor/tree-sitter-java",
    "vendor/tree-sitter-c",
    "vendor/tree-sitter-cpp",
    "vendor/tree-sitter-go",
    "vendor/tree-sitter-rust",
]

def ensure_vendor_repos():
    """
    Make sure grammar repos are cloned under vendor/.
    You can also include them as git submodules instead of cloning here.
    """
    if not os.path.exists("vendor"):
        os.makedirs("vendor")

    repos = {
    "tree-sitter-python":     "https://github.com/tree-sitter/tree-sitter-python",
    "tree-sitter-javascript": "https://github.com/tree-sitter/tree-sitter-javascript",
    "tree-sitter-java":       "https://github.com/tree-sitter/tree-sitter-java",
    "tree-sitter-c":          "https://github.com/tree-sitter/tree-sitter-c",
    "tree-sitter-cpp":        "https://github.com/tree-sitter/tree-sitter-cpp",
    "tree-sitter-go":         "https://github.com/tree-sitter/tree-sitter-go",
    "tree-sitter-rust":       "https://github.com/tree-sitter/tree-sitter-rust",
    }

    for name, url in repos.items():
        path = os.path.join("vendor", name)
        if not os.path.exists(path):
            print(f"Cloning {name}...")
            os.system(f"git clone {url} {path}")
        else:
            print(f"{name} already present, skipping clone.")




def build_library():

    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    print(f"Building {TS_LIB_PATH} with grammars: {GRAMMARS}")
    Language.build_library(
        # Output path
        TS_LIB_PATH,
        # Grammar paths
        GRAMMARS
    )
    print(f"✅ Build complete! Library saved at {TS_LIB_PATH}")


if __name__ == "__main__":
    ensure_vendor_repos()
    build_library()
