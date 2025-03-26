import pytest
import mongomock
import pandas as pd
from entity_data_upload import client, db

@pytest.fixture
def mock_mongo():
    """Fixture to mock MongoDB using mongomock."""
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["Entities"]
    return mock_db

def test_entity_data_upload(mock_mongo, monkeypatch):
    """Test uploading CSV data to MongoDB."""

    # Patch the database with mock database
    monkeypatch.setattr("entity_data_upload.db", mock_mongo)

    # Create dummy data
    test_data = pd.DataFrame({
        "name": ["Entity1", "Entity2"],
        "type": ["Location", "Organization"]
    })

    # Convert to dict and insert into mocked collection
    collection = mock_mongo["Locations"]
    data = test_data.to_dict(orient="records")
    collection.insert_many(data)

    # Assert that data is inserted
    assert collection.count_documents({}) == 2
    assert collection.find_one({"name": "Entity1"})["type"] == "Location"
    assert collection.find_one({"name": "Entity2"})["type"] == "Organization"