from sqlalchemy.engine.url import URL
from sqlalchemy.util import EMPTY_DICT

from backend.app.core.config import Settings
from backend.app.core.schemas.api.db_config import DatabaseURL


def test_settings_from_env_file():
    settings = Settings(_env_file="tests/data/files/test_env")

    assert settings.ALLOWED_HOSTS == ["https://8.8.8.8", "https://5.5.5.5"]


def test_database_url_config():
    url = URL(
        drivername="mysql+psmysql",
        username="root",
        password="123456",
        host="localhost",
        port=3306,
        database="backend",
        query=EMPTY_DICT,
    )
    db_url = DatabaseURL(driver=url.drivername, database="backend", url=url)

    assert isinstance(db_url.url, URL)
    assert db_url.url.render_as_string(hide_password=True) == url.render_as_string(hide_password=True)
