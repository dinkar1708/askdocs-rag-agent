# Intermediate Level: LLM Adapter & Strategy Pattern

---

## 1. Strategy Pattern Implementation

### Q1: How is the provider interface and Ollama adapter implemented?
**Answer:**
In [`app/llm/base.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/llm/base.py) and [`app/llm/ollama_provider.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/llm/ollama_provider.py):

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
import requests

# 1. Base Abstract Class
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response from prompts"""
        pass

# 2. Concrete Ollama Implementation (Local LLM)
class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["message"]["content"]

# 3. Concrete Mock Implementation (Fast Testing)
class MockLLMProvider(BaseLLMProvider):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "This is a mock grounded response for testing. [policy.pdf - Page 1]"
```

---

## 2. Factory Pattern Dispatcher

### Q2: How does the factory select the provider at runtime?
**Answer:**
```python
# app/llm/factory.py
from app.core.config import settings

def get_llm_provider() -> BaseLLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        return OllamaProvider(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)
    elif provider == "gemini":
        from app.llm.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    elif provider == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```
