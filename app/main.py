
from fastapi import FastAPI
from typing import Optional

from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
import numpy as np


from fastapi import BackgroundTasks
import concurrent.futures
import asyncio

import joblib
import pathlib
import pytz
import time
import os
import logging
import pandas as pd
from datetime import datetime

from model_utils.loss_function import lat_lon_loss
from model_utils.holiday_function import SouthAfricanHolidays

from cassandra.cqlengine.management import sync_table

from model_utils.constanst import (
    CRIME_TYPE_MAPPING, HOUR_MAPPINGS, 
    HOLIDAY_MAPPINGS, WEATHER_MAPPINGS)


from . import (
    config, 
    schema,
    models,
    db,
    )

app = FastAPI()

settings  = config.get_settings()


BASE_DIR = pathlib.Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "models"

CRIME_TYPE_PATH = MODEL_DIR / "classfication" / "crime_type_model.pkl"
CRIME_TYPE_ENCODER_PATH = MODEL_DIR / "classfication" / "crime_type_label_encoder.pkl"

CRIME_DENSE_PATH = MODEL_DIR / "neuralnetwork" / "exports" / 'models' / 'neuralnetwork' / 'crime_density'
CRIME_DENSE_SCALER_PATH = MODEL_DIR / "neuralnetwork" / "exports" / 'models' / 'neuralnetwork' / 'crime_density_scaler.pkl'

CRIME_FREQ_PATH = MODEL_DIR / "regression" / "crime_freq_model.pkl"

CRIME_DENSE_MODEL = None
CRIME_TYPE_MODEL = None
CRIME_FREQ_MODEL = None
SA_HOLIDAYS = None
CRIME_DENSE_SCALER = None
CRIME_TYPE_ENCODER = None

PRED_PROB_CRIMETYPE = None
PRED_TYPE_CAT = None

NUM_THREADS = 2
EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS)

DB_SESSION = None
Crime_Density_Table = models.CrimeDensity
Crime_Freq_Table = models.CrimeFreq
Crime_Type_Table = models.CrimeType

SA_TIMEZONE = pytz.timezone("Africa/Johannesburg")
SA_CURRENT_TIME = datetime.now(SA_TIMEZONE)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():

    global DB_SESSION, NUM_THREADS,EXECUTOR, CRIME_DENSE_MODEL, CRIME_FREQ_MODEL, CRIME_TYPE_MODEL, CRIME_TYPE_ENCODER, SA_HOLIDAYS, CRIME_DENSE_SCALER

    if CRIME_DENSE_PATH.exists():
        CRIME_DENSE_MODEL = load_model(CRIME_DENSE_PATH, custom_objects={'lat_lon_loss': lat_lon_loss})

    if CRIME_TYPE_PATH.exists():
        CRIME_TYPE_MODEL = joblib.load(CRIME_TYPE_PATH)

    if CRIME_FREQ_PATH.exists():
        CRIME_FREQ_MODEL = joblib.load(CRIME_FREQ_PATH)

    if CRIME_DENSE_SCALER_PATH.exists():
        CRIME_DENSE_SCALER = joblib.load(CRIME_DENSE_SCALER_PATH)

    CRIME_TYPE_ENCODER = joblib.load(CRIME_TYPE_ENCODER_PATH)

    SA_HOLIDAYS = SouthAfricanHolidays(SA_CURRENT_TIME.year)
    SA_HOLIDAYS.create_holidays_df()

    DB_SESSION = db.get_session()
    sync_table(Crime_Density_Table)
    sync_table(Crime_Freq_Table)
    sync_table(Crime_Type_Table)

    num_cores = os.cpu_count()
    NUM_THREADS = num_cores * 2
    EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS)


def write_to_database(table, latitude, longitude, area, population, holidex_index):
    try:
        table.objects.create(
            **{'x_lat': latitude, 'x_lon': longitude, 'time': str(SA_CURRENT_TIME.date),
            'area': area, 'population': population, 'holiday': holidex_index,
            'temperature': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['temperature'],
            'rainfall': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['rainfall'],}
        )
    except Exception as e:
        logger.error("Error while writing to database: %s", e)

@app.post("/predictCrimeDensity")
async def predict_crime_density(feature: schema.Feature, background_tasks: BackgroundTasks):

    global SA_CURRENT_TIME, SA_HOLIDAYS, HOLIDAY_MAPPINGS, CRIME_DENSE_SCALER, CRIME_DENSE_MODEL

    SA_CURRENT_TIME = datetime.now(SA_TIMEZONE)
    holidex_index = SA_HOLIDAYS.get_sa_holiday(SA_CURRENT_TIME.month, SA_CURRENT_TIME.day)

    input_data = [
        {
            'x_lat': feature.latitude,
            'x_lon': feature.longitude,
            'crime_category': crime_code,
            'month': SA_CURRENT_TIME.month,
            'weekday': SA_CURRENT_TIME.weekday(),
            'day':  SA_CURRENT_TIME.day,
            'time': SA_CURRENT_TIME.hour,
            'temperature': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['temperature'],
            'rainfall': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['rainfall'],
            'holiday':  HOLIDAY_MAPPINGS[holidex_index],
            'population': feature.population,
            'area': feature.area,
        }
        for crime_code in CRIME_TYPE_MAPPING.keys()
    ]
    
    try:
        X_predict_scaled = CRIME_DENSE_SCALER.transform(pd.DataFrame(input_data).values)
        
        def predict_in_thread():
            return CRIME_DENSE_MODEL.predict(X_predict_scaled).tolist()
        
        predicted_coordinates = await asyncio.get_event_loop().run_in_executor(EXECUTOR,
                                                                                predict_in_thread)

        for index, input in enumerate(input_data):
            input['lat'] = predicted_coordinates[index][0]
            input['lon'] = predicted_coordinates[index][1]
            input['crime_category'] = CRIME_TYPE_MAPPING[input['crime_category']]
            input['time'] = HOUR_MAPPINGS[input['time']]
            input['holiday'] = holidex_index

        background_tasks.add_task(write_to_database, Crime_Density_Table, feature.latitude, feature.longitude, 
                                feature.area, feature.population, holidex_index)

        return input_data
    except Exception as e:
        logger.exception("An error occurred during prediction: %s", e)
        return []


@app.post("/predictCrimeType")
async def predict_crime_type(feature: schema.Feature, background_tasks: BackgroundTasks):

    global SA_CURRENT_TIME, SA_HOLIDAYS, HOLIDAY_MAPPINGS, CRIME_TYPE_MODEL, CRIME_TYPE_ENCODER
    
    SA_CURRENT_TIME = datetime.now(SA_TIMEZONE)
    holidex_index = SA_HOLIDAYS.get_sa_holiday(SA_CURRENT_TIME.month, SA_CURRENT_TIME.day)

    input_data = {
            'month': [SA_CURRENT_TIME.month],
            'weekday': [SA_CURRENT_TIME.weekday()],
            'day':  [SA_CURRENT_TIME.day],
            'time': [SA_CURRENT_TIME.hour],
            'lat': [feature.latitude],
            'lon': [feature.longitude],
            'temperature': [WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['temperature']],
            'rainfall': [WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['rainfall']],
            'holiday':  [HOLIDAY_MAPPINGS[holidex_index]],
            'population': [feature.population],
            'area': [feature.area]
        }
    

    try:
        input_data_df = pd.DataFrame(input_data)

        def predict_in_thread():
            PRED_PROB_CRIMETYPE = CRIME_TYPE_MODEL.predict(input_data_df)[0]
            PRED_TYPE_CAT = CRIME_TYPE_ENCODER.inverse_transform(np.arange(len(PRED_PROB_CRIMETYPE)))
            return PRED_PROB_CRIMETYPE, PRED_TYPE_CAT

        PRED_PROB_CRIMETYPE, PRED_TYPE_CAT = await asyncio.get_event_loop().run_in_executor(EXECUTOR, 
                                                                                            predict_in_thread)
        
        input_data_df['time'] = HOUR_MAPPINGS[input_data['time'][0]]
        input_data_df['holiday'] = holidex_index

        result =  { category: probability
                for category, probability in 
                sorted(zip(PRED_TYPE_CAT, PRED_PROB_CRIMETYPE), 
                    key=lambda x: x[1], reverse=True)
                }
        
        result =  [[crime_type, prob, input_data_df.to_dict(orient='list')] for crime_type, prob in result.items()]
        

        background_tasks.add_task(write_to_database, Crime_Type_Table, feature.latitude, feature.longitude,
                                feature.area, feature.population, holidex_index)

        return result
    except Exception as e:
        logger.exception("An error occurred during prediction: %s", e)
        return []


@app.post("/predictCrimeFreq")
async def predict_crime_freq(feature: schema.Feature, background_tasks: BackgroundTasks):
    
    global SA_CURRENT_TIME, SA_HOLIDAYS, HOLIDAY_MAPPINGS, CRIME_FREQ_MODEL
    SA_CURRENT_TIME = datetime.now(SA_TIMEZONE)
    holidex_index = SA_HOLIDAYS.get_sa_holiday(SA_CURRENT_TIME.month, SA_CURRENT_TIME.day)

    input_data = [
        {
            'crime_category': crime_code,
            'month': SA_CURRENT_TIME.month,
            'weekday': SA_CURRENT_TIME.weekday(),
            'day':  SA_CURRENT_TIME.day,
            'time': SA_CURRENT_TIME.hour,
            'lon': feature.longitude,
            'lat': feature.latitude,
            'temperature': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['temperature'],
            'rainfall': WEATHER_MAPPINGS[SA_CURRENT_TIME.month]['rainfall'],
            'holiday':  HOLIDAY_MAPPINGS[holidex_index],
            'population': feature.population,
            'area': feature.area,
        }
        for crime_code in CRIME_TYPE_MAPPING.keys()
       ]

   
    try:
        input_data_df = pd.DataFrame(input_data)

        def predict_in_thread():
            return CRIME_FREQ_MODEL.predict(input_data_df)
        
        crime_freqs = await asyncio.get_event_loop().run_in_executor(EXECUTOR, predict_in_thread)

        result = [{'crime_freq': crime_freq, 
                'holiday': holidex_index,
                'crime_category':CRIME_TYPE_MAPPING[features['crime_category']],
                'time':HOUR_MAPPINGS[features['time']],
                'day': features['day'],
                'weekday': features['weekday'],
                'month': features['month'],
                'temperature': features['temperature'],
                'rainfall':features['rainfall'],
                'lon': feature.longitude,
                'lat': feature.latitude,
                'population': feature.population,
                'area': feature.area}
                for features, crime_freq in zip(input_data, crime_freqs)]
        

        background_tasks.add_task(write_to_database, Crime_Freq_Table, feature.latitude, feature.longitude, 
                                feature.area, feature.population, holidex_index)
        
        return sorted(result, key=lambda x: x['crime_freq'], reverse=True)
    except Exception as e:
        logger.exception("An error occurred during prediction: %s", e)
        return []


@app.get("/apiHealthStatus")
async def check_health():
    return {"status": "OK"}