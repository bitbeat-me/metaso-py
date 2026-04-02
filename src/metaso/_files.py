from __future__ import annotations

from pathlib import Path

from metaso._core import ClientCore
from metaso.types import File


class FilesAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def upload(self, dir_root_id: str, file_path: Path | str) -> File:
        """Upload file to a topic. Requires dirRootId (from topic creation)."""
        return await self._core.backend.upload_file(dir_root_id, Path(file_path))

    async def delete(self, file_id: str) -> bool:
        return await self._core.backend.delete_file(file_id)

    async def progress(self, file_id: str) -> int:
        """Check file processing progress (0-100)."""
        return await self._core.backend.check_file_progress(file_id)
