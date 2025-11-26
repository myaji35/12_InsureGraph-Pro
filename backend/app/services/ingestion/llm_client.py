"""
LLM client wrapper for multiple LLM providers
"""
import json
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import httpx


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Generate response from LLM

        Returns:
            Dict with keys: 'text', 'model', 'confidence'
        """
        pass


class UpstageClient(LLMClient):
    """Client for Upstage Solar API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY not found in environment")

        self.base_url = "https://api.upstage.ai/v1/solar"
        self.model = "solar-pro"

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Generate response from Upstage Solar Pro"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "당신은 보험 약관 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                text = data["choices"][0]["message"]["content"]

                # Extract confidence from response if available
                confidence = 0.85  # Default confidence for Solar Pro

                return {
                    "text": text,
                    "model": self.model,
                    "confidence": confidence,
                }

            except httpx.HTTPError as e:
                raise Exception(f"Upstage API error: {str(e)}")


class OpenAIClient(LLMClient):
    """Client for OpenAI GPT-4o API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o"

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Generate response from OpenAI GPT-4o"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert in analyzing insurance policy documents."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                text = data["choices"][0]["message"]["content"]

                # GPT-4o typically has higher confidence
                confidence = 0.90

                return {
                    "text": text,
                    "model": self.model,
                    "confidence": confidence,
                }

            except httpx.HTTPError as e:
                raise Exception(f"OpenAI API error: {str(e)}")


class LLMClientFactory:
    """Factory for creating LLM clients"""

    @staticmethod
    def create_client(provider: str) -> LLMClient:
        """Create LLM client for specified provider"""
        if provider == "upstage":
            return UpstageClient()
        elif provider == "openai":
            return OpenAIClient()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
