from __future__ import annotations

import uuid
from typing import List, Optional

from .models import FileLink, Project


class ProjectService:
    def build_project(
        self,
        name: str,
        client: str,
        opponent: str,
        lawyer: str,
        stage: str,
        completion: int,
        status: str,
        notes: str,
        file_paths: List[str],
        project_id: Optional[str] = None,
    ) -> Project:
        files = [FileLink.from_path(path) for path in file_paths]
        return Project(
            id=project_id or uuid.uuid4().hex,
            name=name,
            client=client,
            opponent=opponent,
            lawyer=lawyer,
            stage=stage,
            completion=completion,
            status=status,
            notes=notes,
            files=files,
        )
