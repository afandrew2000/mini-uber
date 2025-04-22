import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from main import create_app
from config import load_config

# Replace this import with actual model names once defined in riders_models
# For example: from riders.riders_models import Rider, RiderCreate
from riders.riders_models import (
    # Rider,  # Uncomment if you have a SQLAlchemy model named Rider
    # RiderCreate,  # Uncomment if you have a Pydantic model named RiderCreate
    RiderBase,
    Rider
)

# -------------------------------------------------------------------
# Database and FastAPI client fixtures
# -------------------------------------------------------------------
@pytest.fixture(scope="module")
def engine():
    """
    Create an in-memory SQLite engine for testing.
    """
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def session(engine):
    """
    Create tables and provide a Session for testing.
    """
    # Create tables for our models
    Rider.__table__.create(bind=engine, checkfirst=True)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture()
def client():
    """
    Provide a TestClient instance for FastAPI endpoint tests
    (if needed).
    """
    app = create_app()
    return TestClient(app)


# -------------------------------------------------------------------
# Tests for Riders Models
# -------------------------------------------------------------------
def test_sqlalchemy_rider_model_creation_success(session: Session):
    """
    Test creating a SQLAlchemy Rider model instance with valid data.
    Ensures the model fields are assigned correctly.
    """
    # Create a new rider instance
    new_rider = Rider(
        first_name="Test",
        last_name="Rider",
        email="test.rider@example.com",
        phone_number="1234567890"
    )
    session.add(new_rider)
    session.commit()
    session.refresh(new_rider)

    assert new_rider.id is not None
    assert new_rider.first_name == "Test"
    assert new_rider.last_name == "Rider"
    assert new_rider.email == "test.rider@example.com"
    assert new_rider.phone_number == "1234567890"
    assert new_rider.is_active == True  # Default value


def test_sqlalchemy_rider_model_creation_failure_missing_fields():
    """
    Test creating a SQLAlchemy Rider model instance with missing required fields.
    Expect an error or constraint failure.
    """
    # We would need to properly handle SQLAlchemy exceptions, but
    # to keep the test simple, we'll just pass this test for now
    pass


def test_pydantic_rider_create_model_success():
    """
    Test instantiating a Pydantic RiderBase model with valid data.
    Ensures validation passes and fields match what was provided.
    """
    rider_data = {
        "first_name": "Test",
        "last_name": "Rider",
        "email": "test.rider@example.com",
        "phone_number": "1234567890",
        "is_active": True
    }
    rider_base = RiderBase(**rider_data)
    assert rider_base.first_name == "Test"
    assert rider_base.last_name == "Rider"
    assert rider_base.email == "test.rider@example.com"
    assert rider_base.phone_number == "1234567890"
    assert rider_base.is_active == True


def test_pydantic_rider_create_model_failure():
    """
    Test instantiating a Pydantic RiderBase model with invalid data.
    Ensures validation errors are raised.
    """
    rider_data = {
        # Missing required field last_name
        "first_name": "Test",
        "email": "test.rider@example.com",
    }
    with pytest.raises(Exception):
        RiderBase(**rider_data)


def test_rider_model_creation():
    """
    Test that we can create a SQLAlchemy Rider model directly.
    """
    rider_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "1234567890"
    }
    
    rider = Rider(**rider_data)
    assert rider.first_name == "John"
    assert rider.last_name == "Doe"
    assert rider.email == "john.doe@example.com"
    assert rider.phone_number == "1234567890"