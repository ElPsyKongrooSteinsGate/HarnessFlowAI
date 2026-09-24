from typing import List


class MemoryEngine:
    def __init__(self, storage_uri: str = "sqlite:///memory.db"):
        self.storage_uri = storage_uri
        self._working_memory: List[str] = []

    async def retrieve_relevant(self, query: str) -> List[str]:
        return list(self._working_memory)

    async def save_working_memory(self, key: str, value: str) -> None:
        self._working_memory.append(f"{key}: {value}")

    async def clear(self) -> None:
        self._working_memory.clear()
