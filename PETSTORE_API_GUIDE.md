# Petstore API Guide

## Overview
The Petstore API provides endpoints for managing pet records using Azure Blob Storage as the backend. This API mirrors the appointments structure but uses Blob Storage instead of Cosmos DB.

## Environment Variables Required

Add these to your Function App Configuration:

```
AZURE_STORAGE_CONNECTION_STRING = DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net
# OR alternatively use separate values:
AZURE_STORAGE_ACCOUNT_NAME = your_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY = your_storage_account_key

# Optional (defaults to 'pets')
BLOB_CONTAINER_NAME = pets
```

## API Endpoints

### 1. Create Pet
**POST /api/pets**

Creates a new pet record in Blob Storage.

#### Request Body:
```json
{
  "name": "Fluffy",
  "species": "Cat",
  "breed": "Persian",
  "age": 3,
  "color": "White",
  "weight": 12.5,
  "owner_name": "John Doe",
  "owner_email": "john.doe@email.com",
  "owner_phone": "+1-555-123-4567",
  "medical_notes": "Allergic to certain foods"
}
```

#### Required Fields:
- `name` (string)
- `species` (string)
- `age` (number)
- `owner_name` (string)
- `owner_email` (string)
- `owner_phone` (string)

#### Optional Fields:
- `breed` (string)
- `color` (string)
- `weight` (number)
- `medical_notes` (string)

#### Success Response (201):
```json
{
  "success": true,
  "message": "Pet created successfully",
  "data": {
    "id": "uuid-generated",
    "name": "Fluffy",
    "species": "Cat",
    "breed": "Persian",
    "age": 3,
    "color": "White",
    "weight": 12.5,
    "owner_name": "John Doe",
    "owner_email": "john.doe@email.com",
    "owner_phone": "+1-555-123-4567",
    "medical_notes": "Allergic to certain foods",
    "created_at": "2026-01-22T16:42:59Z",
    "updated_at": "2026-01-22T16:42:59Z"
  }
}
```

### 2. Get All Pets
**GET /api/pets**

Retrieves all pet records from Blob Storage.

#### Optional Query Parameters:
- `limit` (number): Maximum number of pets to return (default: 100, max: 1000)
- `species` (string): Filter pets by species

#### Examples:
```
GET /api/pets
GET /api/pets?limit=50
GET /api/pets?species=cat
GET /api/pets?species=dog&limit=25
```

#### Success Response (200):
```json
{
  "success": true,
  "message": "Retrieved 2 pets successfully",
  "data": [
    {
      "id": "uuid-1",
      "name": "Fluffy",
      "species": "Cat",
      "age": 3,
      "owner_name": "John Doe",
      "created_at": "2026-01-22T16:42:59Z"
    },
    {
      "id": "uuid-2",
      "name": "Rex",
      "species": "Dog",
      "age": 5,
      "owner_name": "Jane Smith",
      "created_at": "2026-01-22T15:30:00Z"
    }
  ],
  "count": 2
}
```

### 3. Delete Pet
**DELETE /api/pets/{id}**

Deletes a pet record by ID.

#### URL Parameters:
- `id` (string): The UUID of the pet to delete

#### Example:
```
DELETE /api/pets/123e4567-e89b-12d3-a456-426614174000
```

#### Success Response (200):
```json
{
  "success": true,
  "message": "Pet with ID 123e4567-e89b-12d3-a456-426614174000 deleted successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Fluffy"
  }
}
```

#### Error Response - Not Found (404):
```json
{
  "success": false,
  "message": "Pet with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

## Blob Storage Architecture

### Container Structure:
- **Container Name:** `pets` (configurable via BLOB_CONTAINER_NAME)
- **File Format:** `{pet-id}.json` (one file per pet)
- **Metadata:** Searchable pet information stored as blob metadata

### Example Blob:
**Filename:** `123e4567-e89b-12d3-a456-426614174000.json`
**Content:** Complete pet JSON data
**Metadata:**
- `pet_name`: "Fluffy"
- `species`: "Cat"
- `breed`: "Persian"
- `owner_name`: "John Doe"
- `created_at`: "2026-01-22T16:42:59Z"

## Validation Rules

### Age Validation:
- Must be a positive integer
- Example: `"age": 3` ✅, `"age": -1` ❌

### Weight Validation (Optional):
- Must be a positive number
- Example: `"weight": 12.5` ✅, `"weight": -5` ❌

### Email Validation:
- Must contain @ symbol
- Example: `"owner_email": "user@example.com"` ✅

### Name Validation:
- Maximum 100 characters
- Required field

### Species Validation:
- Accepts any string but common values include:
- "Dog", "Cat", "Bird", "Fish", "Rabbit", "Hamster", "Guinea Pig", "Reptile", "Other"

## Error Responses

### 400 - Bad Request
```json
{
  "success": false,
  "message": "Missing required fields: name, species, age"
}
```

### 404 - Not Found
```json
{
  "success": false,
  "message": "Pet with ID xyz not found"
}
```

### 500 - Server Error
```json
{
  "success": false,
  "message": "Blob Storage configuration error. Please check environment variables."
}
```

## Testing Examples

### Create a Cat:
```bash
POST /api/pets
Content-Type: application/json

{
  "name": "Whiskers",
  "species": "Cat",
  "breed": "Siamese",
  "age": 2,
  "color": "Gray",
  "weight": 8.0,
  "owner_name": "Alice Johnson",
  "owner_email": "alice.j@email.com",
  "owner_phone": "+1-555-987-6543",
  "medical_notes": "Indoor cat, up to date on vaccinations"
}
```

### Create a Dog:
```bash
POST /api/pets
Content-Type: application/json

{
  "name": "Buddy",
  "species": "Dog",
  "breed": "Golden Retriever",
  "age": 4,
  "color": "Golden",
  "weight": 65.0,
  "owner_name": "Bob Wilson",
  "owner_email": "bob.w@email.com",
  "owner_phone": "+1-555-456-7890",
  "medical_notes": "Very friendly, needs regular exercise"
}
```

## Comparison with Appointments API

| Feature | Appointments API | Petstore API |
|---------|------------------|--------------|
| **Storage** | Cosmos DB | Blob Storage |
| **Data Format** | JSON documents | JSON files |
| **Partitioning** | appointment_date | None (individual files) |
| **Querying** | SQL-like queries | File enumeration + metadata |
| **Scalability** | High (managed NoSQL) | High (object storage) |
| **Cost** | Per RU consumption | Per storage + operations |
| **Consistency** | Strong consistency | Eventual consistency |

## Next Steps

1. **Configure Storage Account** - Set up Azure Storage Account
2. **Add Environment Variables** - Configure connection strings
3. **Test Functions** - Verify all endpoints work
4. **Add to Traffic Generation** - Include in Application Insights availability tests
