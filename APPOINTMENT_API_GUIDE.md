# Pet Clinic Appointment Management API

## Overview

This Azure Functions application provides a RESTful API for managing appointments in a pet clinic system. It uses Azure Cosmos DB as the data store and includes comprehensive validation and error handling.

## Features

- **Create Appointments**: POST endpoint to create new appointments
- **Get All Appointments**: GET endpoint to retrieve all appointments with optional filtering and pagination
- **Get Single Appointment**: GET endpoint to retrieve a specific appointment by ID
- **Cosmos DB Integration**: Uses Azure Cosmos DB with optimized partitioning
- **Data Validation**: Comprehensive input validation using Pydantic models
- **Error Handling**: Proper HTTP status codes and error messages
- **Logging**: Detailed logging for debugging and monitoring

## Architecture

```
├── shared_code/
│   ├── __init__.py
│   ├── models.py          # Pydantic models for data validation
│   └── database.py        # Cosmos DB client and operations
├── CreateAppointment/
│   ├── __init__.py        # POST /api/CreateAppointment
│   └── function.json
├── GetAllAppointments/
│   ├── __init__.py        # GET /api/GetAllAppointments
│   └── function.json
├── GetSingleAppointment/
│   ├── __init__.py        # GET /api/appointments/{id}
│   └── function.json
├── requirements.txt       # Python dependencies
├── host.json             # Azure Functions host configuration
└── README.md
```

## Prerequisites

- Python 3.8 or higher
- Azure Functions Core Tools
- Azure Cosmos DB account
- Azure Functions app (for deployment)

## Environment Variables

Configure the following environment variables in your Azure Functions app:

```bash
COSMOS_DB_ENDPOINT=https://your-cosmosdb-account.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-db-primary-key
COSMOS_DB_DATABASE=petclinic                    # Optional, defaults to 'petclinic'
COSMOS_DB_CONTAINER=appointments                # Optional, defaults to 'appointments'
```

### Local Development (.env file)

Create a `.env` file in the root directory for local development:

```env
COSMOS_DB_ENDPOINT=https://your-cosmosdb-account.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-db-primary-key
COSMOS_DB_DATABASE=petclinic
COSMOS_DB_CONTAINER=appointments
```

## Data Models

### Appointment Structure

```json
{
  "id": "uuid-string",
  "patient_name": "John Doe",
  "patient_email": "john.doe@email.com",
  "patient_phone": "555-0123",
  "doctor_name": "Dr. Smith",
  "appointment_date": "2024-03-15",
  "appointment_time": "14:30",
  "duration_minutes": 30,
  "appointment_type": "Checkup",
  "status": "scheduled",
  "notes": "Regular checkup for Max",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Appointment Statuses

- `scheduled` - Default status for new appointments
- `confirmed` - Appointment confirmed by patient
- `completed` - Appointment completed
- `cancelled` - Appointment cancelled
- `no_show` - Patient didn't show up

## API Endpoints

### 1. Create Appointment

**Endpoint:** `POST /api/CreateAppointment`

**Request Body:**
```json
{
  "patient_name": "John Doe",
  "patient_email": "john.doe@email.com",
  "patient_phone": "555-0123",
  "doctor_name": "Dr. Smith",
  "appointment_date": "2024-03-15",
  "appointment_time": "14:30",
  "duration_minutes": 30,
  "appointment_type": "Checkup",
  "notes": "Regular checkup for Max"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Appointment created successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "patient_name": "John Doe",
    "patient_email": "john.doe@email.com",
    "patient_phone": "555-0123",
    "doctor_name": "Dr. Smith",
    "appointment_date": "2024-03-15",
    "appointment_time": "14:30",
    "duration_minutes": 30,
    "appointment_type": "Checkup",
    "status": "scheduled",
    "notes": "Regular checkup for Max",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Validation Rules:**
- `patient_name`: 2-100 characters
- `patient_email`: 5-100 characters, valid email format
- `patient_phone`: 10-15 characters
- `doctor_name`: 2-100 characters
- `appointment_date`: YYYY-MM-DD format
- `appointment_time`: HH:MM format (24-hour)
- `duration_minutes`: 15-240 minutes (defaults to 30)
- `appointment_type`: 3-50 characters
- `notes`: Optional, max 500 characters

### 2. Get All Appointments

**Endpoint:** `GET /api/GetAllAppointments`

**Query Parameters:**
- `limit` (optional): Number of appointments to return (1-1000, default: 100)
- `offset` (optional): Number of appointments to skip (default: 0)
- `date` (optional): Filter by specific date (YYYY-MM-DD format)

**Examples:**
```bash
# Get all appointments (first 100)
GET /api/GetAllAppointments

# Get appointments with pagination
GET /api/GetAllAppointments?limit=50&offset=100

# Get appointments for specific date
GET /api/GetAllAppointments?date=2024-03-15

# Combined filtering
GET /api/GetAllAppointments?date=2024-03-15&limit=20
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Retrieved 2 appointments successfully",
  "count": 2,
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "patient_name": "John Doe",
      "patient_email": "john.doe@email.com",
      "patient_phone": "555-0123",
      "doctor_name": "Dr. Smith",
      "appointment_date": "2024-03-15",
      "appointment_time": "14:30",
      "duration_minutes": 30,
      "appointment_type": "Checkup",
      "status": "scheduled",
      "notes": "Regular checkup for Max",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 3. Get Single Appointment

**Endpoint:** `GET /api/appointments/{id}?date={appointment_date}`

**Path Parameters:**
- `id`: Appointment UUID

**Query Parameters:**
- `date`: Appointment date (YYYY-MM-DD format) - **Required** for partition key

**Example:**
```bash
GET /api/appointments/123e4567-e89b-12d3-a456-426614174000?date=2024-03-15
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Appointment retrieved successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "patient_name": "John Doe",
    "patient_email": "john.doe@email.com",
    "patient_phone": "555-0123",
    "doctor_name": "Dr. Smith",
    "appointment_date": "2024-03-15",
    "appointment_time": "14:30",
    "duration_minutes": 30,
    "appointment_type": "Checkup",
    "status": "scheduled",
    "notes": "Regular checkup for Max",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Appointment with ID 123e4567-e89b-12d3-a456-426614174000 not found for date 2024-03-15"
}
```

## Error Responses

### Common Error Codes

- **400 Bad Request**: Invalid input data, validation errors
- **404 Not Found**: Appointment not found
- **500 Internal Server Error**: Database connection issues, unexpected errors

### Error Response Format

```json
{
  "success": false,
  "message": "Detailed error message"
}
```

### Example Validation Error

```json
{
  "success": false,
  "message": "Validation error: 1 validation error for CreateAppointmentRequest\npatient_email\n  field required (type=value_error.missing)"
}
```

## Database Configuration

### Cosmos DB Setup

The application automatically creates the database and container if they don't exist:

- **Database Name**: `petclinic` (configurable via `COSMOS_DB_DATABASE`)
- **Container Name**: `appointments` (configurable via `COSMOS_DB_CONTAINER`)
- **Partition Key**: `/appointment_date`
- **Throughput**: 400 RU/s

### Partition Strategy

The application uses `appointment_date` as the partition key, which:
- Distributes data evenly across partitions
- Enables efficient date-based queries
- Supports good performance for typical appointment scheduling patterns

## Local Development

### Setup

1. Clone the repository
2. Set up the virtual environment and install dependencies:
   ```bash
   python3 setup_local_dev.py
   ```
   Or manually:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```
3. Install Azure Functions Core Tools:
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   # Or on macOS: brew tap azure/functions && brew install azure-functions-core-tools@4
   ```
4. Create `.env` file with required environment variables
5. **For VS Code autocomplete**: The `.vscode/settings.json` is already configured to use the virtual environment
6. Start the local development server:
   ```bash
   source .venv/bin/activate
   func start
   ```

### Testing with curl

```bash
# Create appointment
curl -X POST http://localhost:7071/api/CreateAppointment \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "John Doe",
    "patient_email": "john.doe@email.com",
    "patient_phone": "555-0123",
    "doctor_name": "Dr. Smith",
    "appointment_date": "2024-03-15",
    "appointment_time": "14:30",
    "appointment_type": "Checkup"
  }'

# Get all appointments
curl http://localhost:7071/api/GetAllAppointments

# Get single appointment
curl "http://localhost:7071/api/appointments/{appointment-id}?date=2024-03-15"
```

## Deployment

### Azure Functions Deployment

1. Create an Azure Functions app
2. Configure environment variables in the Azure portal
3. Deploy using Azure Functions Core Tools:
   ```bash
   func azure functionapp publish <your-function-app-name>
   ```

### Environment Variables in Azure

Set these in your Azure Functions app configuration:
- `COSMOS_DB_ENDPOINT`
- `COSMOS_DB_KEY`
- `COSMOS_DB_DATABASE` (optional)
- `COSMOS_DB_CONTAINER` (optional)

## Troubleshooting

### Common Issues

1. **Build fails with "requirements.txt not found"**
   - Ensure `requirements.txt` is in the root directory
   - Check that the file is included in your repository

2. **Database connection errors**
   - Verify `COSMOS_DB_ENDPOINT` and `COSMOS_DB_KEY` environment variables
   - Check Cosmos DB account is accessible
   - Ensure firewall settings allow access

3. **Validation errors**
   - Check request body format matches the expected schema
   - Ensure date format is YYYY-MM-DD
   - Ensure time format is HH:MM (24-hour)

4. **Partition key errors**
   - For GetSingleAppointment, ensure `date` query parameter is provided
   - Date must match the appointment's `appointment_date`

### Logging

The application includes comprehensive logging. Check Azure Functions logs for:
- Request processing information
- Database operation results
- Error details and stack traces

### Performance Considerations

- Use pagination for large result sets
- Filter by date when possible to improve query performance
- Monitor Cosmos DB RU consumption
- Consider increasing throughput for high-traffic scenarios

## Security Considerations

- Use Azure Key Vault for storing Cosmos DB connection strings
- Enable authentication on Azure Functions endpoints
- Implement rate limiting for production use
- Validate and sanitize all input data
- Use HTTPS for all API calls
- Consider implementing authentication and authorization

## 🤖 For Future AI Agents / Developers

### ⚠️ CRITICAL KNOWLEDGE BASE MAINTENANCE RULES

**This document (`APPOINTMENT_API_GUIDE.md`) is the SINGLE SOURCE OF TRUTH for the Pet Clinic Appointment Management System.**

#### When You Must Update This Guide:

1. **API Contract Changes**
   - New endpoints added/removed
   - Request/response format changes
   - New query parameters or path parameters
   - Authentication/authorization changes

2. **Data Model Changes**
   - New fields added to appointment model
   - Field validation rules changed
   - Database schema modifications
   - Status enum values changed

3. **Configuration Changes**
   - New environment variables
   - Database connection changes
   - Deployment process updates
   - Security configuration changes

4. **Error Handling Changes**
   - New error codes or messages
   - Error response format changes
   - Validation error modifications

5. **Local Development Changes**
   - Setup process modifications
   - New dependencies
   - VS Code configuration updates
   - Testing procedure changes

#### What To Update:

- **API Endpoint Documentation** - Keep request/response examples current
- **Data Models** - Update JSON schemas and validation rules
- **Environment Variables** - Document all required configuration
- **Setup Instructions** - Ensure setup scripts work correctly
- **Error Examples** - Keep error responses accurate
- **Testing Examples** - Update curl commands and test data
- **Troubleshooting** - Add new known issues and solutions

#### How To Validate Your Updates:

1. **Run the test suite**: `python3 test_functions.py`
2. **Test API examples**: Verify all curl commands in documentation work
3. **Validate setup process**: Test `setup_local_dev.py` on clean environment
4. **Check VS Code autocomplete**: Ensure `.vscode/settings.json` is correct
5. **Review documentation consistency**: Ensure README and API guide align

#### Documentation Standards:

- Use clear, actionable examples
- Include complete request/response bodies
- Document all optional parameters
- Provide troubleshooting for common issues
- Keep error messages up-to-date with actual implementation
- Maintain consistent formatting and structure

**REMEMBER: If it's not documented here, other agents won't know it exists!**

## Next Steps / Future Enhancements

- Add appointment update/cancel functionality
- Implement appointment scheduling conflict detection
- Add patient and doctor management endpoints
- Implement email notifications
- Add appointment reminders
- Include audit logging
- Add comprehensive unit and integration tests
- Implement caching for frequently accessed data

### 📝 When Adding New Features:

1. **Implement the feature**
2. **Update this API guide immediately**
3. **Add new API endpoints to the summary table**
4. **Update data models if changed**
5. **Add example requests/responses**
6. **Update troubleshooting section if needed**
7. **Run and update tests**
8. **Update README.md if architecture changes**
