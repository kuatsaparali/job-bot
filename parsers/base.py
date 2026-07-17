from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Optional, List

class Vacancy(BaseModel):
    external_id: str
    title: str
    company: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    currency: Optional[str] = None
    city: Optional[str] = None
    description_raw: Optional[str] = None
    url: str

class BaseParser(ABC):
    @abstractmethod
    async def parse(self, query: str, limit: int = 20) -> List[Vacancy]:
        pass