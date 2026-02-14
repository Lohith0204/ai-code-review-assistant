import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path before importing app modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.services.rag_orchestrator import RAGOrchestrator
from app.core.models import ReviewResult

@patch("app.services.reviewer.code_reviewer.OpenAI")
def test_workflow(mock_openai):
    # Setup Mock
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = """
    {
        "summary": "Code looks good but has some minor issues.",
        "risks": ["Potential off-by-one error in loop"],
        "suggestions": ["Use enumerate() instead of range(len())"],
        "affected_files": ["app/services/chunking/code_chunker.py"]
    }
    """
    mock_client.chat.completions.create.return_value = mock_completion

    print("Initializing RAG Orchestrator...")
    orchestrator = RAGOrchestrator()
    
    # Use a small known directory relative to this test file
    target_dir = str(Path(__file__).parent.parent / "app" / "services" / "chunking")
    
    print(f"Running review on {target_dir}...")
    result = orchestrator.run_review(target_dir, query="Check for off-by-one errors")
    
    print("\n--- Review Result ---")
    print(f"Summary: {result.summary}")
    print(f"Risks: {result.risks}")
    
    # Behavioral Assertions
    assert isinstance(result, ReviewResult)
    assert len(result.summary) > 0
    assert "off-by-one" in result.risks[0]
    
    print("\n✅ Test Passed: RAG pipeline is operational (OpenAI mocked).")

if __name__ == "__main__":
    test_workflow()
