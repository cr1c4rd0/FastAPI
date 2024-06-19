from fastapi import FastAPI, Path, Query, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security.http import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Coroutine, Optional, List
from jwt_manager import create_token, validate_token
from fastapi.security import HTTPBearer
from config.database import Session, engine, Base
from models.movie import Movie as MovieModel
from fastapi.encoders import jsonable_encoder
from middlewares.error_handler import ErrorHandler

app = FastAPI()
app.title = "Mi aplicación con FastAPI"
app.version = "0.0.1"

app.add_middleware(ErrorHandler)

Base.metadata.create_all(bind=engine)
    

class User(BaseModel):
    email: str
    password: str

# Validación de tipos de datos con Pydantic
class Movie(BaseModel):
    id: Optional[int] = None
    title: str = Field(min_length=5, max_length=15) # validación del la cantidad de caracteres para el titulo de la pelicula y el minimo que se requiera, adicionalmente pone un titulo por defecto
    overview: str = Field(min_length=15, max_length=50)
    year: int = Field(le=2022) # permite poner el año minimo requerido usando le
    rating: float = Field(ge=1, le=10)
    category: str = Field(min_length=5, max_length=15)

    # con esta clase puedo crear los valores por defecto
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Mi película",
                "overview": "Descripción de película",
                "year": 2022,
                "rating": 9.8,
                "category": "Acción"
            }
        }


movies = [
    {
        "id": 1,
      		"title": "Avatar",
      		"overview": "En un exuberante planeta llamado Pandora viven los Na'vi, seres que ...",
      		"year": "2009",
      		"rating": 7.8,
      		"category": "AcciÃ³n"
    },
    {
        "id": 2,
      		"title": "Avatar",
      		"overview": "En un exuberante planeta llamado Pandora viven los Na'vi, seres que ...",
      		"year": "2009",
      		"rating": 7.8,
      		"category": "AcciÃ³n"
    }
]

@app.post('/login', tags=['auth'])
def login(user: User):
    if user.email == "admin@gmail.com" and user.password == "admin":
        token: str = create_token(user.dict())
    return JSONResponse(status_code=200, content=token)

@app.get('/', tags=['home'])
def message():
    return HTMLResponse('<h1>Hello World</h1>')


@app.get('/movies', tags=['movies'], response_model=List[Movie], status_code=200, dependencies=[Depends(JWTBearer)])
def get_movies() -> List[Movie]:
    db = Session()
    result = db.query(MovieModel).all() # ponemos la el nombre de la tabla que queremos consultar o el modelo
    return JSONResponse(status_code=200, content=jsonable_encoder(result))


@app.get('/movies/{id}', tags=['movies'], response_model=Movie)
def get_movie(id: int = Path(ge=1, le=2000)): # validación de párametros con Pydantic usando Path()
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first() # metodo filter para la busqueda y filtrado de peliculas
    if not result:
        JSONResponse(status_code=404, content={'message': 'No encontrado'})
    return JSONResponse(status_code=404, content=jsonable_encoder(result))


@app.get('/movies/', tags=['movies'], response_model=List[Movie])
# validación de párametros con Pydantic usando Query()
def get_movies_by_category(category: str = Query(min_length=5, max_length=15)) -> List[Movie]:
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.category == category).all()
    return JSONResponse(status_code=200, content=jsonable_encoder(result))


@app.post('/movies', tags=['movies'], response_model=dict, status_code=201)
def create_movie(movie: Movie) -> dict:
    # creo una session para conectarme a la BD
    db = Session()
    new_movie = MovieModel(**movie.dict())
    db.add(new_movie)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "Se ha regitrado la película"})


@app.put('/movies/{id}', tags=['movies'], response_model=dict, status_code=200)
def update_movie(id: int, movie: Movie) -> dict:
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first()
    if not result:
        return JSONResponse(status_code=404, content={"message": "No se ha encontrado"})
    result.title = movie.title
    result.overview = movie.overview
    result.year = movie.year
    result.rating = movie.rating
    result.category = movie.category
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Se ha modificado la película"})

@app.delete('/movies/{id}', tags=['movies'], response_model=dict, status_code=200)
def delete_movie(id: int) -> dict:
    db = Session()
    result = db.query(MovieModel).filter(MovieModel.id == id).first()
    if not result:
        return JSONResponse(status_code=404, content={"message": "No se ha encontrado"})
    db.delete(result)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Se ha eliminado la película"})
