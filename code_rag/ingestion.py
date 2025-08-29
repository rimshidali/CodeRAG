# ingestion.py
import os
import tempfile
import subprocess
from pathlib import Path
from typing import List, Tuple


class CodeIngestion:
    def __init__(self, repo_url: str = None, local_path: str = None):
        """
        Initialize ingestion with either a GitHub repo URL or a local path.
        """
        self.repo_url = repo_url
        self.local_path = local_path
        self.clone_dir = None

    def clone_repo(self) -> str:
        """
        Clone the GitHub repo into a temp directory.
        """
        if not self.repo_url:
            raise ValueError("Repo URL not provided!")

        self.clone_dir = tempfile.mkdtemp()
        print(f"Cloning {self.repo_url} into {self.clone_dir}")
        subprocess.run(["git", "clone", self.repo_url, self.clone_dir], check=True)
        return self.clone_dir

    def get_code_files(self, path: str) -> List[str]:
        """
        Collect all code files from a given directory.
        You can filter extensions as per your use case.
        """
        extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",".md",
                      ".txt", ".json", ".yaml", ".toml"]
        code_files = []
        for p in Path(path).rglob("*"):
            if p.is_file() and p.suffix in extensions:
                code_files.append(str(p))
        return code_files
    



    def read_files(self, files: List[str]) -> List[Tuple[str, str]]:
        """
        Read the contents of code files.
        Returns a list of tuples: (file_path, file_content)
        """
        file_contents = []
        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    file_contents.append((f, file.read()))
            except Exception as e:
                print(f"Could not read {f}: {e}")
        return file_contents

    def ingest(self) -> List[Tuple[str, str]]:
        """
        Main entry point: clone (if needed), collect files, return their contents.
        """
        base_path = self.local_path or self.clone_repo()
        files = self.get_code_files(base_path)
        print(f"Found {len(files)} code files")
        return self.read_files(files)
