from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import config


engine = create_engine(config.SQLITE_DB_URI)

def get_session() -> Session:
    with Session(engine) as session:
        yield session
