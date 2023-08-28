import uuid
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class CrimeDensity(Model):
    __keyspace__ = "model_inferences"
    uuid = columns.UUID(
                         primary_key=True,
                         default=uuid.uuid1
                         )

    time = columns.Text()
    holiday = columns.Text()

    population = columns.Float()
    area  = columns.Float()
    temperature = columns.Float()
    rainfall = columns.Float()
    x_lat = columns.Float()
    x_lon = columns.Float()


class CrimeType(Model):
    __keyspace__ = "model_inferences"
    uuid = columns.UUID(
                         primary_key=True,
                         default=uuid.uuid1
                         )

    time = columns.Text()
    holiday = columns.Text()

    population = columns.Float()
    area  = columns.Float()
    temperature = columns.Float()
    rainfall = columns.Float()
    x_lat = columns.Float()
    x_lon = columns.Float()

class CrimeFreq(Model):
    __keyspace__ = "model_inferences"
    uuid = columns.UUID(
                         primary_key=True,
                         default=uuid.uuid1
                         )

    time = columns.Text()
    holiday = columns.Text()

    population = columns.Float()
    area  = columns.Float()
    temperature = columns.Float()
    rainfall = columns.Float()
    x_lat = columns.Float()
    x_lon = columns.Float()

              
