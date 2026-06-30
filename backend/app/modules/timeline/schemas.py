from datetime import datetime

from pydantic import BaseModel


class TimelineItem(BaseModel):
    module: str
    entity_type: str
    id: str
    title: str
    occurred_at: datetime
    route: str
