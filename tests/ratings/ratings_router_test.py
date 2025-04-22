import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the FastAPI application factory and config loader
from main import create_app
from config import load_config

# Import the service functions that will be called inside the router
# (We will mock these in our tests)
from ratings.ratings_service import (
    rate_driver,
    rate_rider,
    get_rider_rating,
    get_driver_rating,
)


@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient using the FastAPI app.
    """
    # Create a test-specific FastAPI app
    app = FastAPI()
    
    # Add validation exception handler for test compatibility
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
    
    # Import the ratings router
    from ratings.ratings_router import router as ratings_router
    app.include_router(ratings_router)
    
    return TestClient(app)


@pytest.fixture
def test_db():
    """
    Mock or set up a test database session.
    Cleanup after tests if needed.
    """
    # In a real test, you might create an in-memory DB or use a temporary file DB
    # and yield a SQLAlchemy session.
    # For demonstration, just yield None to fulfill the fixture requirement.
    yield None


@pytest.mark.describe("Ratings Router - POST /ratings/driver -> rate_driver_endpoint")
class TestRateDriverEndpoint:
    @pytest.mark.it("Successfully rate a driver with valid payload")
    def test_rate_driver_success(self, client, mocker):
        """
        Should return 200 OK when rating a driver successfully.
        """
        # Arrange
        mock_rate_driver = mocker.patch("ratings.ratings_service.rate_driver", return_value=True)
        payload = {"ride_id": 123, "rating": 5, "review": "Great driver!"}

        # Act
        response = client.post("/ratings/driver", json=payload)

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_rate_driver.assert_called_once_with(123, 5, "Great driver!")

    @pytest.mark.it("Fail to rate a driver with missing parameters")
    def test_rate_driver_missing_params(self, client, mocker):
        """
        Should return 422 Unprocessable Entity (or 400) when required fields are missing.
        """
        mocker.patch("ratings.ratings_service.rate_driver")
        payload = {"ride_id": 123, "rating": 5}
        # Missing 'review'
        response = client.post("/ratings/driver", json=payload)

        assert response.status_code in [400, 422]  # Depending on validation settings


@pytest.mark.describe("Ratings Router - POST /ratings/rider -> rate_rider_endpoint")
class TestRateRiderEndpoint:
    @pytest.mark.it("Successfully rate a rider with valid payload")
    def test_rate_rider_success(self, client, mocker):
        """
        Should return 200 OK when rating a rider successfully.
        """
        mock_rate_rider = mocker.patch("ratings.ratings_service.rate_rider", return_value=True)
        payload = {"ride_id": 456, "rating": 4, "review": "Pleasant experience"}

        response = client.post("/ratings/rider", json=payload)

        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_rate_rider.assert_called_once_with(456, 4, "Pleasant experience")

    @pytest.mark.it("Fail to rate a rider with invalid rating data")
    def test_rate_rider_invalid_rating(self, client, mocker):
        """
        Should return 422 or 400 for invalid rating (e.g., negative or above max).
        """
        mocker.patch("ratings.ratings_service.rate_rider")
        payload = {"ride_id": 456, "rating": 999, "review": "Impossible rating"}

        response = client.post("/ratings/rider", json=payload)

        assert response.status_code in [400, 422]


@pytest.mark.describe("Ratings Router - GET /ratings/rider/{rider_id} -> get_rider_rating_endpoint")
class TestGetRiderRatingEndpoint:
    @pytest.mark.it("Retrieve rider rating successfully when record exists")
    def test_get_rider_rating_success(self, client, mocker):
        """
        Should return a valid rating when a rider has ratings.
        """
        mock_get_rider_rating = mocker.patch("ratings.ratings_service.get_rider_rating", return_value=4.5)

        rider_id = 777
        response = client.get(f"/ratings/rider/{rider_id}")

        assert response.status_code == 200
        assert response.json()["rating"] == 4.5
        mock_get_rider_rating.assert_called_once_with(rider_id)

    @pytest.mark.it("Return a valid response when rider has no ratings")
    def test_get_rider_rating_no_ratings(self, client, mocker):
        """
        Should handle a scenario where the rider does not have any ratings yet.
        """
        mocker.patch("ratings.ratings_service.get_rider_rating", return_value=None)
        rider_id = 888

        response = client.get(f"/ratings/rider/{rider_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 0  # Or some default value that the endpoint might return


@pytest.mark.describe("Ratings Router - GET /ratings/driver/{driver_id} -> get_driver_rating_endpoint")
class TestGetDriverRatingEndpoint:
    @pytest.mark.it("Retrieve driver rating successfully when record exists")
    def test_get_driver_rating_success(self, client, mocker):
        """
        Should return a valid rating when a driver has ratings.
        """
        mock_get_driver_rating = mocker.patch("ratings.ratings_service.get_driver_rating", return_value=4.8)

        driver_id = 999
        response = client.get(f"/ratings/driver/{driver_id}")

        assert response.status_code == 200
        assert response.json()["rating"] == 4.8
        mock_get_driver_rating.assert_called_once_with(driver_id)

    @pytest.mark.it("Handle no ratings for driver gracefully")
    def test_get_driver_rating_no_ratings(self, client, mocker):
        """
        Should handle the case where the driver does not have any ratings.
        """
        mocker.patch("ratings.ratings_service.get_driver_rating", return_value=None)
        driver_id = 1000

        response = client.get(f"/ratings/driver/{driver_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 0  # Or some default/no-rating indicator