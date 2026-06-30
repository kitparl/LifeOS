from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.career.repository import CareerRepository
from app.modules.career.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    CareerProfileResponse,
    CareerProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


class CareerService:
    def __init__(self, db: AsyncSession):
        self.repo = CareerRepository(db)

    async def get_profile(self, user_id: str) -> CareerProfileResponse:
        profile = await self.repo.get_or_create_profile(user_id)
        return CareerProfileResponse.model_validate(profile)

    async def update_profile(self, user_id: str, data: CareerProfileUpdate) -> CareerProfileResponse:
        profile = await self.repo.get_or_create_profile(user_id)
        updated = await self.repo.update_profile(profile, data)
        return CareerProfileResponse.model_validate(updated)

    async def list_projects(self, user_id: str) -> list[ProjectResponse]:
        return [ProjectResponse.model_validate(p) for p in await self.repo.list_projects(user_id)]

    async def get_project(self, user_id: str, project_id: str) -> ProjectResponse:
        project = await self.repo.get_project(user_id, project_id)
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        return ProjectResponse.model_validate(project)

    async def create_project(self, user_id: str, data: ProjectCreate) -> ProjectResponse:
        project = await self.repo.create_project(user_id, data)
        return ProjectResponse.model_validate(project)

    async def update_project(self, user_id: str, project_id: str, data: ProjectUpdate) -> ProjectResponse:
        project = await self.repo.get_project(user_id, project_id)
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        updated = await self.repo.update_project(project, data)
        return ProjectResponse.model_validate(updated)

    async def delete_project(self, user_id: str, project_id: str) -> None:
        project = await self.repo.get_project(user_id, project_id)
        if not project:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
        await self.repo.delete_project(project)

    async def list_applications(self, user_id: str) -> list[ApplicationResponse]:
        return [ApplicationResponse.model_validate(a) for a in await self.repo.list_applications(user_id)]

    async def get_application(self, user_id: str, app_id: str) -> ApplicationResponse:
        app = await self.repo.get_application(user_id, app_id)
        if not app:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        return ApplicationResponse.model_validate(app)

    async def create_application(self, user_id: str, data: ApplicationCreate) -> ApplicationResponse:
        app = await self.repo.create_application(user_id, data)
        return ApplicationResponse.model_validate(app)

    async def update_application(self, user_id: str, app_id: str, data: ApplicationUpdate) -> ApplicationResponse:
        app = await self.repo.get_application(user_id, app_id)
        if not app:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        updated = await self.repo.update_application(app, data)
        return ApplicationResponse.model_validate(updated)

    async def delete_application(self, user_id: str, app_id: str) -> None:
        app = await self.repo.get_application(user_id, app_id)
        if not app:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        await self.repo.delete_application(app)

    async def analytics(self, user_id: str) -> dict:
        apps = await self.repo.list_applications(user_id)
        projects = await self.repo.list_projects(user_id)
        by_status: dict[str, int] = {}
        for a in apps:
            by_status[a.status] = by_status.get(a.status, 0) + 1
        return {
            "total_projects": len(projects),
            "total_applications": len(apps),
            "applications_by_status": by_status,
        }
