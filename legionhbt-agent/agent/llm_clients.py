import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai
import anthropic
import aiohttp


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    finish_reason: str


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = "gpt-4o"
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                content="[OpenAI not configured. Set OPENAI_API_KEY environment variable.]",
                model=self.model,
                tokens_used=0,
                finish_reason="error"
            )
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_used=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def generate_async(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, prompt, system_prompt, temperature, max_tokens)


class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.model = "claude-3-5-sonnet-20241022"
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                content="[Anthropic not configured. Set ANTHROPIC_API_KEY environment variable.]",
                model=self.model,
                tokens_used=0,
                finish_reason="error"
            )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )
    
    async def generate_async(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, prompt, system_prompt, temperature, max_tokens)


class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
    
    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                content="[DeepSeek not configured. Set DEEPSEEK_API_KEY environment variable.]",
                model=self.model,
                tokens_used=0,
                finish_reason="error"
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        import requests
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.model,
            tokens_used=data["usage"]["total_tokens"],
            finish_reason=data["choices"][0].get("finish_reason", "stop")
        )
    
    async def generate_async(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 4000) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                data = await response.json()
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=self.model,
                    tokens_used=data["usage"]["total_tokens"],
                    finish_reason=data["choices"][0].get("finish_reason", "stop")
                )


class LLMRouter:
    def __init__(self):
        self.clients = {
            "openai": OpenAIClient(),
            "anthropic": AnthropicClient(),
            "deepseek": DeepSeekClient()
        }
        self.fallback_order = ["openai", "anthropic", "deepseek"]
    
    def generate(self, prompt: str, system_prompt: str = "", preferred_provider: str = "openai", temperature: float = 0.7) -> LLMResponse:
        providers = [preferred_provider] + [p for p in self.fallback_order if p != preferred_provider]
        
        for provider in providers:
            try:
                client = self.clients.get(provider)
                if client:
                    return client.generate(prompt, system_prompt, temperature)
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
    
    async def generate_async(self, prompt: str, system_prompt: str = "", preferred_provider: str = "openai", temperature: float = 0.7) -> LLMResponse:
        providers = [preferred_provider] + [p for p in self.fallback_order if p != preferred_provider]
        
        for provider in providers:
            try:
                client = self.clients.get(provider)
                if client:
                    return await client.generate_async(prompt, system_prompt, temperature)
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
