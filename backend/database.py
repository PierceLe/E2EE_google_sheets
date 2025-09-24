from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import app_config

host = app_config["DATABASE"]["MYSQL"]["HOST"]
port = app_config["DATABASE"]["MYSQL"]["PORT"]
username = app_config["DATABASE"]["MYSQL"]["USERNAME"]
password = app_config["DATABASE"]["MYSQL"]["PASSWORD"]
database = app_config["DATABASE"]["MYSQL"]["DATABASE"]

# Database connection URI (replace with your actual MySQL credentials)
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(username, password, host, port, database)

# Create an engine that will interact with the MySQL database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    pool_size=50,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=300,
    pool_pre_ping=True,
    query_cache_size=0
)

# Create a base class for our models
Base = declarative_base()

# SessionLocal: A session that interacts with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=True)

Base.metadata.create_all(bind=engine)  # Add DDL here


# Dependency to get the database session in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
