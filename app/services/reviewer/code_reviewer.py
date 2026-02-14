from openai import OpenAI
from app.core.models import ReviewResult
import json

class ReviewService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def review_code(self, context_chunks: str) -> ReviewResult:
        prompt = (
            "You are a senior software engineer performing a code review.\n"
            "Analyze the following code context and provide structured feedback.\n"
            "Return ONLY a JSON object with keys: 'summary', 'risks' (list), 'suggestions' (list), 'affected_files' (list).\n"
            "Do not return markdown formatting like ```json ... ```, just the raw JSON string.\n\n"
            f"Code Context:\n{context_chunks}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        
        # Cleanup potential markdown fencing just in case
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            data = json.loads(content)
            return ReviewResult(**data)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return ReviewResult(
                summary="Error parsing AI response",
                risks=["AI returned non-JSON format"],
                suggestions=["Check logs for raw response"],
                affected_files=[]
            )
