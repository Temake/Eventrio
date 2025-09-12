from .base import *
import os
from dotenv import load_dotenv
load_dotenv()
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('PROD_DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}