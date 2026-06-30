from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.career.models import CareerProfile, CareerProject, JobApplication
from app.modules.career.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    CareerProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
)


class CareerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: str) -> CareerProfile:
        result = await self.db.execute(select(CareerProfile).where(CareerProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile:
            return profile
        profile = CareerProfile(user_id=user_id)
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update_profile(self, profile: CareerProfile, data: CareerProfileUpdate) -> CareerProfile:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def list_projects(self, user_id: str) -> list[CareerProject]:
        result = await self.db.execute(
            select(CareerProject).where(CareerProject.user_id == user_id).order_by(CareerProject.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_project(self, user_id: str, project_id: str) -> CareerProject | None:
        result = await self.db.execute(
            select(CareerProject).where(CareerProject.id == project_id, CareerProject.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_project(self, user_id: str, data: ProjectCreate) -> CareerProject:
        project = CareerProject(user_id=user_id, **data.model_dump())
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_project(self, project: CareerProject, data: ProjectUpdate) -> CareerProject:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project: CareerProject) -> None:
        await self.db.delete(project)

    async def list_applications(self, user_id: str) -> list[JobApplication]:
        result = await self.db.execute(
            select(JobApplication).where(JobApplication.user_id == user_id).order_by(JobApplication.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_application(self, user_id: str, app_id: str) -> JobApplication | None:
        result = await self.db.execute(
            select(JobApplication).where(JobApplication.id == app_id, JobApplication.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_application(self, user_id: str, data: ApplicationCreate) -> JobApplication:
        app = JobApplication(user_id=user_id, **data.model_dump())
        self.db.add(app)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def update_application(self, app: JobApplication, data: ApplicationUpdate) -> JobApplication:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(app, key, value)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def delete_application(self, app: JobApplication) -> None:
        await self.db.delete(app)
