from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import requests
from typing import List

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Travel Planner API")

def validate_external_place(external_id: int):
    url = f"https://api.artic.edu/api/v1/artworks/{external_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Place with external ID {external_id} does not exist in Art Institute API"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Third-party API is unavailable"
        )


@app.post("/projects", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    if project.places and len(project.places) > 10:
        raise HTTPException(status_code=400, detail="A project can contain a maximum of 10 places")

    db_project = models.Project(name=project.name, description=project.description, start_date=project.start_date)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    if project.places:
        seen_ids = set()
        for p in project.places:
            if p.external_id in seen_ids:
                continue
            seen_ids.add(p.external_id)
            validate_external_place(p.external_id)
            db_place = models.Place(external_id=p.external_id, notes=p.notes, project_id=db_project.id)
            db.add(db_place)
        db.commit()
        db.refresh(db_project)

    return db_project


@app.get("/projects", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project(project_id: int, updated_project: schemas.ProjectBase, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = updated_project.name
    project.description = updated_project.description
    project.start_date = updated_project.start_date
    db.commit()
    db.refresh(project)
    return project


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for place in project.places:
        if place.is_visited:
            raise HTTPException(status_code=400,
                                detail="Cannot delete project if any of its places are already visited")

    db.delete(project)
    db.commit()
    return None


@app.post("/projects/{project_id}/places", response_model=schemas.PlaceResponse, status_code=status.HTTP_201_CREATED)
def add_place_to_project(project_id: int, place: schemas.PlaceCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if len(project.places) >= 10:
        raise HTTPException(status_code=400, detail="Project has reached the maximum limit of 10 places")

    exists = db.query(models.Place).filter(models.Place.project_id == project_id,
                                           models.Place.external_id == place.external_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="This place is already added to this project")

    validate_external_place(place.external_id)

    db_place = models.Place(external_id=place.external_id, notes=place.notes, project_id=project_id)
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place


@app.put("/projects/{project_id}/places/{place_id}", response_model=schemas.PlaceResponse)
def update_place(project_id: int, place_id: int, u_place: schemas.NoteUpdate, db: Session = Depends(get_db)):
    place = db.query(models.Place).filter(models.Place.id == place_id, models.Place.project_id == project_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found within this project")

    if u_place.notes is not None:
        place.notes = u_place.notes
    if u_place.is_visited is not None:
        place.is_visited = u_place.is_visited

    db.commit()
    db.refresh(place)
    return place


@app.get("/projects/{project_id}/places", response_model=List[schemas.PlaceResponse])
def list_places_for_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.places


@app.get("/projects/{project_id}/places/{place_id}", response_model=schemas.PlaceResponse)
def get_single_place(project_id: int, place_id: int, db: Session = Depends(get_db)):
    place = db.query(models.Place).filter(models.Place.id == place_id, models.Place.project_id == project_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found within this project")
    return place