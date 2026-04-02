from __future__ import annotations

from pathlib import Path

from metaso._core import ClientCore
from metaso.types import File


class FilesAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def upload(self, topic_id: str, file_path: Path | str) -> File:
        return await self._core.backend.upload_file(topic_id, Path(file_path))

    async def list(self, topic_id: str) -> list[File]:
        return await self._core.backend.list_files(topic_id)

    async def delete(self, file_id: str) -> bool:
        return await self._core.backend.delete_file(file_id)
