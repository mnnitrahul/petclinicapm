# 🏥 PetClinic APM - Complete API Knowledge Base

## Overview
This Azure Functions application provides a complete Pet Clinic Appointment and Pet Management system with both **Cosmos DB** (appointments) and **Azure Blob Storage** (pets) backends.

## 🔧 **CRITICAL: Azure Functions Cold Start Fix**

### ❌ **Previous Issue: 500 Internal Server Error**
- **Root Cause**: Network calls during `__init__` caused Azure Functions worker crashes during cold start
- **Problem**: Both `CosmosDBClient` and `BlobStorageClient` were making network calls in constructors
- **Result**: Functions never reached `main()`, platform returned HTTP 500

### ✅ **Solution: Lazy Initialization**
- **No network calls in `__init__`** - Store configuration only
- **No logging in constructors** - Azure Functions sensitive during startup  
- **Lazy client creation** - Clients created only when first operation happens
- **Container/database creation deferred** - Happens on first API call, not during import

---

## 🐕 Pet Management API (Azure Blob Storage)

### Architecture
- **Storage**: Individual JSON files per pet in Azure Blob Storage
- **Container**: `pets` (configurable via `BLOB_CONTAINER_NAME`)
- **Metadata**: Pet name, species, breed, owner for efficient searching
- **File naming**: `{pet_id}.json`

### Environment Variables
```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=petstore;AccountKey=...;EndpointSuffix=core.windows.net
BLOB_CONTAINER_NAME=pets  # Optional, defaults to "pets"
```

### **1. Create Pet** 
**Endpoint**: `POST /api/pets`

**Request Body**:
```json
{
  "name": "Buddy",
  "species": "Dog", 
  "breed": "Golden Retriever",
  "age": 5,
  "color": "Golden",
  "weight": 65.5,
  "owner_name": "John Smith",
  "owner_email": "john@example.com",
  "owner_phone": "+1-555-123-4567",
  "medical_notes": "Healthy dog, up to date on vaccines"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Pet created successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Buddy",
    "species": "Dog",
    "breed": "Golden Retriever", 
    "age": 5,
    "color": "Golden",
    "weight": 65.5,
    "owner_name": "John Smith",
    "owner_email": "john@example.com",
    "owner_phone": "+1-555-123-4567",
    "medical_notes": "Healthy dog, up to date on vaccines",
    "created_at": "2026-01-22T22:45:00Z",
    "updated_at": "2026-01-22T22:45:00Z"
  }
}
```

**Validation Rules**:
- `name`, `species`, `age`, `owner_name`, `owner_email`, `owner_phone`: Required
- `age`: Must be positive integer
- `weight`: Must be positive number (if provided)
- `owner_email`: Must contain '@' symbol
- `name`: Max 100 characters

### **2. Get All Pets**
**Endpoint**: `GET /api/pets`

**Query Parameters**:
- `limit` (optional): Max number of pets to return (default: 100, max: 1000)
- `species` (optional): Filter by species (case-insensitive)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Retrieved 15 pets successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Buddy", 
      "species": "Dog",
      "age": 5,
      "owner_name": "John Smith",
      "created_at": "2026-01-22T22:45:00Z"
    }
  ],
  "count": 15
}
```

### **3. Get Single Pet**
**Endpoint**: `GET /api/pets/{pet_id}`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Pet retrieved successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Buddy",
    "species": "Dog",
    "breed": "Golden Retriever",
    "age": 5,
    "color": "Golden", 
    "weight": 65.5,
    "owner_name": "John Smith",
    "owner_email": "john@example.com",
    "owner_phone": "+1-555-123-4567",
    "medical_notes": "Healthy dog, up to date on vaccines",
    "created_at": "2026-01-22T22:45:00Z",
    "updated_at": "2026-01-22T22:45:00Z"
  }
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Pet not found"
}
```

### **4. Delete Pet**
**Endpoint**: `DELETE /api/pets/{pet_id}`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Pet deleted successfully"
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Pet not found"
}
```

---

## 📅 Appointment Management API (Cosmos DB)

### Architecture
- **Database**: Azure Cosmos DB
- **Database Name**: `petclinic` (configurable via `COSMOS_DB_DATABASE`)
- **Container**: `appointments` (configurable via `COSMOS_DB_CONTAINER`) 
- **Partition Key**: `/appointment_date` for optimal query performance
- **Throughput**: 400 RU/s

### Environment Variables
```bash
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-primary-key-here==
COSMOS_DB_DATABASE=petclinic  # Optional, defaults to "petclinic"
COSMOS_DB_CONTAINER=appointments  # Optional, defaults to "appointments"
```

### **1. Create Appointment**
**Endpoint**: `POST /api/appointments`

**Request Body**:
```json
{
  "patient_name": "Buddy",
  "patient_email": "owner@example.com", 
  "patient_phone": "+1-555-123-4567",
  "doctor_name": "Dr. Smith",
  "appointment_date": "2026-02-15",
  "appointment_time": "14:30",
  "duration_minutes": 30,
  "appointment_type": "checkup",
  "notes": "Annual wellness check"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Appointment created successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001", 
    "patient_name": "Buddy",
    "patient_email": "owner@example.com",
    "patient_phone": "+1-555-123-4567",
    "doctor_name": "Dr. Smith",
    "appointment_date": "2026-02-15",
    "appointment_time": "14:30", 
    "duration_minutes": 30,
    "appointment_type": "checkup",
    "status": "scheduled",
    "notes": "Annual wellness check",
    "created_at": "2026-01-22T22:45:00Z",
    "updated_at": "2026-01-22T22:45:00Z"
  }
}
```

**Validation Rules**:
- All fields required except `notes` and `duration_minutes`
- `appointment_date`: Must be YYYY-MM-DD format
- `appointment_time`: Must be HH:MM format (24-hour)
- `duration_minutes`: Defaults to 30
- `status`: Always set to "scheduled" on creation

### **2. Get All Appointments**
**Endpoint**: `GET /api/appointments`

**Query Parameters**:
- `limit` (optional): Max appointments to return (default: 100)
- `offset` (optional): Skip first N appointments for pagination (default: 0)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Retrieved 25 appointments successfully",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "patient_name": "Buddy",
      "doctor_name": "Dr. Smith", 
      "appointment_date": "2026-02-15",
      "appointment_time": "14:30",
      "status": "scheduled",
      "appointment_type": "checkup",
      "created_at": "2026-01-22T22:45:00Z"
    }
  ],
  "count": 25
}
```

### **3. Get Single Appointment**
**Endpoint**: `GET /api/appointments/{appointment_id}`

**Query Parameters**:
- `appointment_date`: Required for Cosmos DB partition key

**Example**: `GET /api/appointments/550e8400-e29b-41d4-a716-446655440001?appointment_date=2026-02-15`

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Appointment retrieved successfully", 
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_name": "Buddy",
    "patient_email": "owner@example.com",
    "patient_phone": "+1-555-123-4567", 
    "doctor_name": "Dr. Smith",
    "appointment_date": "2026-02-15",
    "appointment_time": "14:30",
    "duration_minutes": 30,
    "appointment_type": "checkup",
    "status": "scheduled",
    "notes": "Annual wellness check",
    "created_at": "2026-01-22T22:45:00Z",
    "updated_at": "2026-01-22T22:45:00Z"
  }
}
```

---

## 🧪 Debug & Testing

### **Debug Blob Storage**
**Endpoint**: `GET /api/debug-blob`

**Purpose**: Always returns HTTP 200 with detailed debugging information for blob storage issues.

**Response**:
```json
{
  "message": "🔍 Blob Storage Debug function completed",
  "status": "SUCCESS",
  "timestamp": "2026-01-22T22:45:00Z",
  "imports": {
    "azure_storage_blob": "SUCCESS"
  },
  "environment_variables": {
    "AZURE_STORAGE_CONNECTION_STRING": "✅ YES",
    "connection_string_length": 141,
    "BLOB_CONTAINER_NAME": "pets"
  },
  "connection_test": {
    "method": "azure_sdk",
    "blob_storage_client_init": "SUCCESS"
  },
  "diagnosis": [
    "✅ Azure Storage Blob SDK available",
    "✅ Connection string configured", 
    "✅ Using official Azure Storage Blob SDK",
    "✅ BlobStorageClient initialization successful",
    "🎉 All blob storage tests passed!"
  ],
  "detailed_errors": []
}
```

### **Local Testing**

#### **Mock Tests** (No Azure connection required):
```bash
python3 local_test_mock.py
```

#### **Full Integration Tests** (Requires Azure credentials):
```bash
export AZURE_STORAGE_CONNECTION_STRING='your-connection-string'
python3 local_test.py
```

---

## 🚀 Deployment Guide

### **Requirements**
```txt
azure-functions==1.18.0
azure-cosmos==4.3.1
azure-identity==1.14.1
azure-storage-blob==12.19.0
python-dateutil==2.8.2
```

### **Environment Setup**
1. **Azure Storage Account** for pets
2. **Azure Cosmos DB Account** for appointments  
3. **Azure Functions App** with Python 3.9+ runtime

### **Environment Variables**
```bash
# Blob Storage (Required for Pet APIs)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
BLOB_CONTAINER_NAME=pets

# Cosmos DB (Required for Appointment APIs)  
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-key-here==
COSMOS_DB_DATABASE=petclinic
COSMOS_DB_CONTAINER=appointments
```

### **Function Keys**
Get function keys for API access:
```bash
az functionapp keys list --name your-function-app --resource-group your-rg
```

---

## 📊 API Status Codes

| Status | Meaning |
|--------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request data |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

---

## 🔍 Troubleshooting

### **Common Issues**

#### **500 Internal Server Error**
- **Cause**: Network calls during Azure Functions cold start
- **Solution**: Use lazy initialization (implemented in current version)

#### **Missing Environment Variables**
- **Error**: "Database configuration error" 
- **Solution**: Check all required environment variables are set

#### **Cosmos DB Connection Issues**
- **Error**: "Database connection error"
- **Solution**: Verify `COSMOS_DB_ENDPOINT` and `COSMOS_DB_KEY` are correct

#### **Blob Storage Authentication Issues**
- **Error**: "Blob Storage configuration error"
- **Solution**: Verify `AZURE_STORAGE_CONNECTION_STRING` format and credentials

### **Debug Steps**
1. **Test debug endpoint**: `GET /api/debug-blob`
2. **Check function logs** in Azure Portal
3. **Verify environment variables** in Function App settings
4. **Run local tests** to isolate issues

---

## 🎯 Performance & Best Practices

### **Pet Management (Blob Storage)**
- **Efficient**: Individual JSON files with metadata for fast searching
- **Scalable**: No limit on number of pets
- **Cost-effective**: Pay only for storage used
- **Search optimization**: Use species metadata for filtering

### **Appointment Management (Cosmos DB)**
- **Optimized partition key**: `/appointment_date` for query performance
- **Cross-partition queries**: Enabled for flexible searching
- **Pagination**: Use `limit` and `offset` parameters
- **Cost management**: 400 RU/s throughput for moderate load

### **Azure Functions Best Practices**
- ✅ **Lazy initialization**: No network calls in constructors  
- ✅ **Error handling**: Comprehensive try/catch blocks
- ✅ **Logging**: Structured logging for debugging
- ✅ **Validation**: Input validation with clear error messages
- ✅ **Status codes**: Proper HTTP status codes
- ✅ **Response format**: Consistent JSON response structure

---

## 📝 Example Usage

### **Complete Workflow**
```bash
# 1. Create a new pet
curl -X POST https://your-function-app.azurewebsites.net/api/pets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Buddy",
    "species": "Dog",
    "age": 5,
    "owner_name": "John Smith", 
    "owner_email": "john@example.com",
    "owner_phone": "+1-555-123-4567"
  }'

# 2. Get all pets
curl https://your-function-app.azurewebsites.net/api/pets

# 3. Create appointment for pet
curl -X POST https://your-function-app.azurewebsites.net/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Buddy",
    "patient_email": "john@example.com",
    "patient_phone": "+1-555-123-4567",
    "doctor_name": "Dr. Smith", 
    "appointment_date": "2026-02-15",
    "appointment_time": "14:30",
    "appointment_type": "checkup"
  }'

# 4. Get all appointments
curl https://your-function-app.azurewebsites.net/api/appointments
```

---

*This knowledge base covers the complete PetClinic APM API with both pet management and appointment booking functionality, optimized for Azure Functions with proper cold start handling.*
