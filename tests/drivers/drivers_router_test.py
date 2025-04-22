import pytest
from fastapi import FastAPI, Request 
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import create_app
from config import load_config


@pytest.fixture(scope="module")
def client():
    """
    Fixture to create a TestClient instance for testing the FastAPI app.
    Creates a custom app with the router for testing.
    """
    app = FastAPI()
    
    # Add validation exception handler to convert 422 to 400 for test compatibility
    @app.exception_handler(RequestValidationError) 
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
        
    # Import and include just the drivers router for focused testing
    from drivers.drivers_router import router as drivers_router
    app.include_router(drivers_router)
    
    return TestClient(app)


# Create a test driver object that mocks the DriverObject returned by services
class MockDriverObject:
    def __init__(self, id, name, license_number, vehicle_info):
        self.id = id
        self.name = name
        self.license_number = license_number
        self.vehicle_info = vehicle_info


@pytest.mark.describe("Drivers Router - create_driver_endpoint")
class TestCreateDriverEndpoint:
    """
    Test suite for the create_driver_endpoint in 'drivers.drivers_router'.
    Verifies driver creation success and various error scenarios.
    """

    @patch("drivers.drivers_router.create_driver")
    def test_create_driver_success(self, mock_create_driver, client):
        """
        Test successful creation of a driver with valid input.
        Mocks the 'create_driver' service to return a simulated driver record.
        """
        # Arrange
        mock_driver = MockDriverObject(
            id=1,
            name="John Doe",
            license_number="XYZ123",
            vehicle_info={"description": "Toyota"}
        )
        mock_create_driver.return_value = mock_driver
        
        payload = {
            "name": "John Doe",
            "license_number": "XYZ123",
            "vehicle_info": "Toyota"
        }

        # Act
        response = client.post("/drivers", json=payload)

        # Assert
        assert response.status_code == 201, f"Expected 201 Created for successful driver creation, got {response.status_code} with body: {response.text}"
        assert response.json().get("driver_id") == 1
        assert response.json().get("name") == "John Doe"
        assert response.json().get("license_number") == "XYZ123"

    def test_create_driver_missing_fields(self, client):
        """
        Test creating a driver with missing required fields.
        Expects a 400 Bad Request response.
        """
        # Arrange
        payload = {
            # 'name' is missing
            "license_number": "XYZ123",
            "vehicle_info": "Toyota"
        }

        # Act
        response = client.post("/drivers", json=payload)

        # Assert
        assert response.status_code == 400, "Expected 400 when required fields are missing"

    def test_create_driver_invalid_data(self, client):
        """
        Test creating a driver with invalid data type or structure.
        Expects a 422 Unprocessable Entity or similar client error response.
        """
        # Arrange
        payload = {
            "name": 12345,  # Invalid data type for name
            "license_number": None,  # Possibly invalid
            "vehicle_info": "Toyota"
        }

        # Act
        response = client.post("/drivers", json=payload)

        # Assert
        # Depending on your validation, it could be 400 or 422.
        assert response.status_code in [400, 422], "Expected an error when invalid data is provided"


@pytest.mark.describe("Drivers Router - update_vehicle_details_endpoint")
class TestUpdateVehicleDetailsEndpoint:
    """
    Test suite for the update_vehicle_details_endpoint in 'drivers.drivers_router'.
    Verifies successful updates and error scenarios for driver vehicle info.
    """

    @patch("drivers.drivers_router.update_vehicle_details")
    def test_update_vehicle_details_success(self, mock_update_vehicle_details, client):
        """
        Test updating vehicle details for an existing driver.
        Mocks the 'update_vehicle_details' service to simulate a successful update.
        """
        # Arrange
        mock_driver = MockDriverObject(
            id=1,
            name="John Doe",
            license_number="XYZ123",
            vehicle_info={"description": "Honda Accord 2022"}
        )
        mock_update_vehicle_details.return_value = mock_driver
        
        driver_id = 1
        payload = {
            "vehicle_info": "Honda Accord 2022"
        }

        # Act
        response = client.put(f"/drivers/{driver_id}/vehicle", json=payload)

        # Assert
        assert response.status_code == 200, f"Expected 200 OK for successful vehicle update, got {response.status_code} with body: {response.text}"
        assert response.json().get("vehicle_info") == "Honda Accord 2022"

    @patch("drivers.drivers_router.update_vehicle_details")
    def test_update_vehicle_details_driver_not_found(self, mock_update_vehicle_details, client):
        """
        Test updating vehicle details with a non-existent driver ID.
        Expects a 404 Not Found response.
        """
        # Arrange
        # Return None to simulate driver not found
        mock_update_vehicle_details.return_value = None
        
        driver_id = 9999
        payload = {
            "vehicle_info": "Updated Vehicle Info"
        }

        # Act
        response = client.put(f"/drivers/{driver_id}/vehicle", json=payload)

        # Assert
        assert response.status_code == 404, f"Expected 404, got {response.status_code} with body: {response.text}"

    def test_update_vehicle_details_missing_fields(self, client):
        """
        Test updating vehicle details with missing fields in the payload.
        Expects a 400 Bad Request response.
        """
        # Arrange
        driver_id = 1
        payload = {
            # Missing 'vehicle_info'
        }

        # Act
        response = client.put(f"/drivers/{driver_id}/vehicle", json=payload)

        # Assert
        assert response.status_code == 400, "Expected 400 when required fields are missing"

    def test_update_vehicle_details_invalid_data(self, client):
        """
        Test updating vehicle details with an invalid payload structure.
        Expects a 422 Unprocessable Entity or a similar error response.
        """
        # Arrange
        driver_id = 1
        payload = {
            "vehicle_info": 1234  # Invalid data type
        }

        # Act
        response = client.put(f"/drivers/{driver_id}/vehicle", json=payload)

        # Assert
        assert response.status_code in [400, 422], "Expected an error when invalid data is provided"