from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .models import Project
from .storage import JsonStorage


class ProjectRepository:
    def __init__(self, data_file: Path) -> None:
        self.storage = JsonStorage(data_file)

    def list(self) -> List[Project]:
        data = self.storage.load()
        projects = [Project.from_dict(item) for item in data]
        projects.sort(key=lambda item: item.updated_at or item.created_at, reverse=True)
        return projects

    def get(self, project_id: str) -> Optional[Project]:
        for project in self.list():
            if project.id == project_id:
                return project
        return None

    def add(self, project: Project) -> None:
        project.ensure_defaults()
        projects = self.list()
        projects.insert(0, project)
        self._save(projects)

    def update(self, project: Project) -> None:
        project.ensure_defaults()
        projects = self.list()
        updated = False
        for index, existing in enumerate(projects):
            if existing.id == project.id:
                projects[index] = project
                updated = True
                break
        if not updated:
            projects.insert(0, project)
        self._save(projects)

    def delete(self, project_id: str) -> bool:
        projects = self.list()
        filtered = [project for project in projects if project.id != project_id]
        if len(filtered) == len(projects):
            return False
        self._save(filtered)
        return True

    def delete_all(self) -> int:
        """删除所有项目，返回删除的数量"""
        projects = self.list()
        count = len(projects)
        self._save([])
        return count

    def _save(self, projects: List[Project]) -> None:
        data = [project.to_dict() for project in projects]
        self.storage.save(data)
