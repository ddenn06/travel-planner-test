from pydantic import BaseModel
from typing import List, Optional

class PlaceBase(BaseModel):
    external_id: int
    notes: Optional[str] = None

class PlaceCreate(PlaceBase):
    pass

class PlaceResponse(PlaceBase):
    id: int
    is_visited: bool
    project_id: int

    class Config:
        from_attributes = True

class NoteUpdate(BaseModel):
    notes: Optional[str] = None
    is_visited: Optional[bool] = None

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None

class ProjectCreate(ProjectBase):
    places: Optional[List[PlaceCreate]] = []

class ProjectResponse(ProjectBase):
    id: int
    places: List[PlaceResponse] = []

    class Config:
        from_attributes = True