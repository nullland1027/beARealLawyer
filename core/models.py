from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from .enums import STATUSES


@dataclass
class FileLink:
    path: str
    name: str
    extension: str
    is_folder: bool = False

    @classmethod
    def from_path(cls, path: str) -> "FileLink":
        file_path = Path(path)
        name = file_path.name if file_path.name else path
        is_folder = file_path.is_dir() if file_path.exists() else False
        extension = "" if is_folder else file_path.suffix.lower()
        return cls(path=path, name=name, extension=extension, is_folder=is_folder)

    def icon(self) -> str:
        if self.is_folder:
            return "📁"
        mapping = {
            ".pdf": "📕",
            ".doc": "📝",
            ".docx": "📝",
            ".xls": "📊",
            ".xlsx": "📊",
            ".ppt": "📈",
            ".pptx": "📈",
            ".txt": "📄",
            ".zip": "🗜️",
            ".rar": "🗜️",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
        }
        return mapping.get(self.extension, "📄")

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "is_folder": self.is_folder,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileLink":
        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            extension=data.get("extension", ""),
            is_folder=data.get("is_folder", False),
        )


@dataclass
class Project:
    id: str
    name: str
    client: str
    opponent: str
    lawyer: str
    stage: str
    completion: int
    status: str
    notes: str
    files: List[FileLink] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def ensure_defaults(self) -> None:
        if self.status not in STATUSES:
            self.status = STATUSES[0]
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "client": self.client,
            "opponent": self.opponent,
            "lawyer": self.lawyer,
            "stage": self.stage,
            "completion": self.completion,
            "status": self.status,
            "notes": self.notes,
            "files": [file.to_dict() for file in self.files],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        files = [FileLink.from_dict(item) for item in data.get("files", [])]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            client=data.get("client", ""),
            opponent=data.get("opponent", ""),
            lawyer=data.get("lawyer", ""),
            stage=data.get("stage", ""),
            completion=int(data.get("completion", 0) or 0),
            status=data.get("status", STATUSES[0]),
            notes=data.get("notes", ""),
            files=files,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
