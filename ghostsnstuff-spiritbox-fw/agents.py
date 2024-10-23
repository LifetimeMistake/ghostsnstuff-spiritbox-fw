from typing import Self
from openai import OpenAI
from pydantic import BaseModel

class BaseAgent:
    def __init__(self, client: OpenAI, model: str, temperature: float, response_schema: BaseModel, prompt: str) -> Self:
        self.client = client
        self.model = model
        self.temperature = temperature
        self.schema = response_schema
        self.prompt = prompt
        
    def ask(self, question: str) -> BaseModel:
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": question}
        ]
        
        response = self.client.beta.chat.completions.parse(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            response_format=self.schema
        )
        
        return response.choices[0].message.parsed