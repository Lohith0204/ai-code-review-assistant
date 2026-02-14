import os
from pathlib import Path
from typing import List
from fastapi import HTTPException
from app.core.models import FileMetadata

class FileIngestionService:
    def __init__(self):
        # Configure limits from environment variables with sensible defaults
        self.max_files = int(os.getenv("MAX_FILES", 50))
        self.max_file_size_kb = int(os.getenv("MAX_FILE_SIZE_KB", 500))
        self.max_total_size_mb = int(os.getenv("MAX_TOTAL_SIZE_MB", 2))

    def load_directory(self, root_path: str) -> List[FileMetadata]:
        code_files = []
        total_size = 0
        file_count = 0
        
        # Convert MB to bytes
        max_total_bytes = self.max_total_size_mb * 1024 * 1024
        # Convert KB to bytes
        max_file_bytes = self.max_file_size_kb * 1024

        for path in Path(root_path).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".js", ".java", ".ts", ".tsx", ".jsx"}:
                file_count += 1
                if file_count > self.max_files:
                    raise HTTPException(
                        status_code=413, 
                        detail=f"Repository too large: limit is {self.max_files} files."
                    )

                try:
                    file_bytes = path.stat().st_size
                    if file_bytes > max_file_bytes:
                        continue # Skip oversized files instead of failing the whole thing? 
                        # Or raise error for strictness? Let's be strict for security.
                        # raise HTTPException(status_code=413, detail=f"File {path.name} exceeds {self.max_file_size_kb}KB limit.")
                    
                    total_size += file_bytes
                    if total_size > max_total_bytes:
                        raise HTTPException(
                            status_code=413, 
                            detail=f"Repository too large: total size exceeds {self.max_total_size_mb}MB limit."
                        )

                    content = path.read_text(encoding="utf-8", errors="ignore")
                    code_files.append(
                        FileMetadata(
                            path=str(path),
                            language=path.suffix[1:],
                            content=content,
                            size_bytes=file_bytes
                        )
                    )
                except Exception as e:
                    print(f"Error reading {path}: {e}")
        
        if not code_files:
            raise HTTPException(status_code=400, detail="No supported code files found in the repository.")
            
        return code_files
