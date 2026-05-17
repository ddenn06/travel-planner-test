from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    start_date = Column(String, nullable=True)

    places = relationship("Place", back_populates="project", cascade="all, delete-orphan")


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, index=True)  # ID з Art Institute API
    notes = Column(String, nullable=True)
    is_visited = Column(Boolean, default=False)

    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="places")