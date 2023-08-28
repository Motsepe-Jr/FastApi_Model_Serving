from functools import lru_cache
from pydantic import  Field
from pydantic_settings import BaseSettings
import os



os.environ['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = "1"

class Settings(BaseSettings):
    ASTRA_DB_CLIENT_ID: str = Field(..., env="ASTRA_DB_CLIENT_ID")
    ASTRA_DB_SECRET: str = Field(..., env="ASTRA_DB_SECRET")
    
    ASTRA_DB_TOKEN: str = Field(..., env="ASTRA_DB_TOKEN")
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    BUCKET_NAME: str = Field(..., env="BUCKET_NAME")
    ENDPOINT_URL: str = Field(..., env="ENDPOINT_URL")
    REGION_NAME: str = Field(..., env="REGION_NAME")

    class Config:
        env_file = '.env'

@lru_cache
def get_settings():
    return Settings()




