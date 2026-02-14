from typing import List
from app.core.models import FileMetadata, CodeChunk

class ChunkingService:
    def chunk_files(self, files: List[FileMetadata], chunk_size: int = 500) -> List[CodeChunk]:
        all_chunks = []
        for file in files:
            chunks = self._chunk_single_file(file, chunk_size)
            all_chunks.extend(chunks)
        return all_chunks

    def _chunk_single_file(self, file: FileMetadata, chunk_size: int) -> List[CodeChunk]:
        chunks = []
        lines = file.content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        # Simple line-based chunking for now, can be improved to AST-based later
        # We estimate chunk_size in characters, but here we process by lines to keep it simple and safe for line numbers
        # A better approach for "chunk_size=500" (tokens/chars) with line tracking:
        
        current_chunk_lines = []
        current_char_count = 0
        start_line = 1
        chunk_index = 0

        for i, line in enumerate(lines, start=1):
            current_chunk_lines.append(line)
            current_char_count += len(line) + 1 # +1 for newline

            if current_char_count >= chunk_size or i == total_lines:
                chunk_content = "\n".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        file_path=file.path,
                        start_line=start_line,
                        end_line=i,
                        language=file.language,
                        content=chunk_content,
                        chunk_index=chunk_index
                    )
                )
                # Reset
                current_chunk_lines = []
                current_char_count = 0
                start_line = i + 1
                chunk_index += 1
        
        return chunks
