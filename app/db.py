from . import config
import pathlib

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine import connection

BASE_DIR = pathlib.Path(__file__).resolve().parent


SOURCE_DIR = BASE_DIR / "ignored" 
if not SOURCE_DIR.exists():
    SOURCE_DIR = BASE_DIR / 'decrypted'

CLUSTER_BUNDLE = str(SOURCE_DIR / 'astradb_connect.zip')


settings = config.get_settings()
CLIENT_ID = settings.ASTRA_DB_CLIENT_ID
CLIENT_SECRET = settings.ASTRA_DB_SECRET


def get_cluster():
    cloud_config = {
         'secure_connect_bundle': CLUSTER_BUNDLE
    }
    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    return cluster


def get_session():
    cluster = get_cluster()
    session = cluster.connect()
    connection.register_connection(str(session), session=session)
    connection.set_default_connection(str(session))
    return session
