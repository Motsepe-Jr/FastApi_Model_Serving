from pydantic import BaseModel

class Feature(BaseModel):
    latitude: float
    longitude:float
    area: float
    population: float