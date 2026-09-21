import psycopg2
import random

PG_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "insurance_db",
    "user": "insurance_user", "password": "insurance_pw",
}

conn = psycopg2.connect(**PG_CONFIG)