from pydantic import BaseModel, Field
from typing import List, Optional

class FileMetadata(BaseModel):
    """Metadata for a source code file."""
    path: str
    language: str
    content: str
    size_bytes: int

class CodeChunk(BaseModel):
    """A chunk of code with lineage metadata."""
    file_path: str
    start_line: int
    end_line: int
    language: str
    content: str
    chunk_index: int
    
class ReviewResult(BaseModel):
    """Structured review output."""
    summary: str
    risks: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)

class ReviewRequest(BaseModel):
    """Request payload for code review."""
    directory_path: str = Field(..., description="Absolute path to the local repository to review")
    query: str = Field(default="Identify bugs and security risks", description="Specific focus for the review")

class PRReviewRequest(BaseModel):
    """Request payload for GitHub PR review."""
    repo_url: str = Field(..., description="GitHub repository (e.g., 'owner/repo')")
    pr_number: int = Field(..., description="Pull request number")
    github_token: str = Field(..., description="GitHub personal access token")
    query: str = Field(default="Review for bugs, security issues, and code quality", description="Review focus")

class PRReviewComment(BaseModel):
    """A review comment for a specific file and line."""
    path: str = Field(..., description="File path relative to repo root")
    line: int = Field(..., description="Line number for the comment")
    body: str = Field(..., description="Comment text")

class PRReviewResult(BaseModel):
    """Result of a PR review."""
    summary: str
    comments_posted: int
    files_reviewed: List[str]
    risks: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    review_url: Optional[str] = None
