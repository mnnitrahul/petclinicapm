# Pet Clinic Appointment Management System

[![Azure Functions](https://img.shields.io/badge/Azure-Functions-blue)](https://azure.microsoft.com/en-us/services/functions/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![Cosmos DB](https://img.shields.io/badge/Database-Cosmos%20DB-purple)](https://azure.microsoft.com/en-us/services/cosmos-db/)

A comprehensive RESTful API for managing pet clinic appointments built with Azure Functions and Cosmos DB.

## 🚀 Quick Start

This project provides three core appointment management functions:
- **Create Appointments** - Add new appointments with full validation
- **Get All Appointments** - Retrieve appointments with pagination and filtering  
- **Get Single Appointment** - Fetch specific appointments by ID

## 📚 **Complete Documentation**

👉 **For detailed API documentation, setup instructions, and development guide, see:**

### **[APPOINTMENT_API_GUIDE.md](APPOINTMENT_API_GUIDE.md)**

This comprehensive guide includes:
- Complete API endpoint specifications
- Request/response examples  
- Database setup and configuration
- Local development setup
- Deployment instructions
- Troubleshooting guide
- Security considerations

## ⚡ Quick Setup for Development

1. **Install dependencies and setup environment:**
   ```bash
   python3 setup_local_dev.py
   ```

2. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Configure environment variables** (see [API Guide](APPOINTMENT_API_GUIDE.md#environment-variables))

4. **Start local development:**
   ```bash
   func start
   ```

## 🧪 Test Your Setup

```bash
source .venv/bin/activate
python3 test_functions.py
```

Should return: `🎉 All tests passed! Your Azure Functions are ready for deployment.`

## 🏗️ Architecture Overview

```
├── shared_code/              # Shared models and database logic
├── CreateAppointment/        # POST endpoint for creating appointments
├── GetAllAppointments/       # GET endpoint for listing appointments  
├── GetSingleAppointment/     # GET endpoint for single appointment
├── .vscode/                  # VS Code configuration for autocomplete
├── requirements.txt          # Python dependencies
├── host.json                 # Azure Functions configuration (REQUIRED for deployment)
└── APPOINTMENT_API_GUIDE.md  # 📖 MAIN DOCUMENTATION
```

## 🔑 Key Features

- ✅ **Comprehensive Validation** - Pydantic models with field validation
- ✅ **Cosmos DB Integration** - Optimized partitioning and queries
- ✅ **Error Handling** - Proper HTTP status codes and messages
- ✅ **Pagination Support** - Efficient handling of large datasets
- ✅ **Local Development** - Full VS Code autocomplete support
- ✅ **Production Ready** - Logging, monitoring, and security considerations

## 🌐 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/CreateAppointment` | Create a new appointment |
| `GET` | `/api/GetAllAppointments` | Get all appointments with optional filtering |
| `GET` | `/api/appointments/{id}` | Get a specific appointment by ID |

## 📋 Appointment Data Model

```json
{
  "id": "uuid",
  "patient_name": "John Doe",
  "patient_email": "john.doe@email.com", 
  "patient_phone": "555-012-3456",
  "doctor_name": "Dr. Smith",
  "appointment_date": "2024-03-15",
  "appointment_time": "14:30", 
  "duration_minutes": 30,
  "appointment_type": "Checkup",
  "status": "scheduled",
  "notes": "Optional notes",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## 🚨 Important Notes

### For Future Developers/Agents

**⚠️ CRITICAL: When making changes to this system:**

1. **Always update the [APPOINTMENT_API_GUIDE.md](APPOINTMENT_API_GUIDE.md)** when making design changes
2. **The API Guide is the single source of truth** for this system
3. **Run tests after changes:** `python3 test_functions.py` 
4. **Update examples in documentation** if API contracts change
5. **Maintain backward compatibility** or document breaking changes

### Knowledge Base Maintenance

This repository uses `APPOINTMENT_API_GUIDE.md` as its comprehensive knowledge base. Any agent working on this project should:

- **Reference the API Guide first** for understanding the system
- **Update the API Guide immediately** after making any changes
- **Keep examples current** with actual implementation
- **Document all environment variables** and configuration changes
- **Update troubleshooting section** with new known issues

## 🔍 Distributed Tracing (APIM Integration)

### ⚠️ Critical: Trace Context Propagation

When Azure Functions are behind API Management (APIM) with Application Insights enabled, **you must explicitly propagate the trace context** to maintain end-to-end tracing.

**Without proper propagation:**
- APIM and Function traces have different `operation_Id` values
- Application Map shows disconnected nodes
- End-to-end transaction search doesn't work

### Required Implementation

Every HTTP-triggered function must include this at the start:

```python
from shared_code.telemetry import get_trace_context
from opentelemetry import context

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Extract and attach trace context from APIM
    if get_trace_context:
        ctx = get_trace_context(req)
        context.attach(ctx)
    
    # Rest of your function code...
```

### How It Works

1. APIM sends `traceparent` header: `00-{trace_id}-{span_id}-{flags}`
2. `get_trace_context()` extracts this W3C trace context
3. `context.attach()` sets it as the current context
4. All downstream calls (Cosmos DB, Blob Storage) inherit this trace ID

### Validate Traces in Application Insights

**Query to check if traces are properly connected:**

```kql
// Find requests from APIM and their downstream dependencies
let apimRequests = requests
| where timestamp > ago(1h)
| where cloud_RoleName == "petclinic-apim"  // or your APIM name
| project operation_Id, apim_timestamp = timestamp, apim_name = name;

let functionRequests = requests
| where timestamp > ago(1h)
| where cloud_RoleName in ("petclinic-apm-function-app", "petclinic-apm-function-app2")
| project operation_Id, func_timestamp = timestamp, func_name = name;

let dependencies = dependencies
| where timestamp > ago(1h)
| where cloud_RoleName in ("petclinic-apm-function-app", "petclinic-apm-function-app2")
| project operation_Id, dep_timestamp = timestamp, dep_target = target, dep_type = type;

// Join to see if they share the same operation_Id
apimRequests
| join kind=inner functionRequests on operation_Id
| join kind=inner dependencies on operation_Id
| project operation_Id, apim_name, func_name, dep_target, dep_type
| take 50
```

**If traces are broken (different operation_Id), you'll see:**
- Empty results from the join
- APIM requests with one operation_Id
- Function requests with a different operation_Id

**Query to find broken traces:**

```kql
// Find function requests that DON'T have matching APIM requests
requests
| where timestamp > ago(1h)
| where cloud_RoleName in ("petclinic-apm-function-app", "petclinic-apm-function-app2")
| join kind=leftanti (
    requests
    | where timestamp > ago(1h)
    | where cloud_RoleName == "petclinic-apim"
) on operation_Id
| project timestamp, name, operation_Id, cloud_RoleName
| order by timestamp desc
| take 20
```

### Expected Trace Flow

```
APIM Request (operation_Id: abc123)
└── Function Request (operation_Id: abc123)  ← Same ID = CORRECT
    └── Cosmos DB HTTP (operation_Id: abc123)
    └── Blob Storage HTTP (operation_Id: abc123)
```

### Common Mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| Missing `get_trace_context` import | Broken traces | Add import from `shared_code.telemetry` |
| Not calling `context.attach()` | Broken traces | Call after `get_trace_context(req)` |
| Attaching context after async call | Partial traces | Attach context at function start |
| `ENABLE_OPENTELEMETRY=false` | No OTel traces | Remove or set to `true` |

---

## 🤝 Contributing

1. Review the [API Guide](APPOINTMENT_API_GUIDE.md) to understand the system
2. Make your changes
3. Run tests: `python3 test_functions.py`
4. **Update documentation** in `APPOINTMENT_API_GUIDE.md`
5. Test your changes locally with `func start`

## 📞 Support

- Check the [Troubleshooting Guide](APPOINTMENT_API_GUIDE.md#troubleshooting) first
- Review [Common Issues](APPOINTMENT_API_GUIDE.md#common-issues) 
- For VS Code autocomplete issues, see [Local Development Setup](APPOINTMENT_API_GUIDE.md#local-development)

---

**📖 For complete documentation, examples, and troubleshooting: [APPOINTMENT_API_GUIDE.md](APPOINTMENT_API_GUIDE.md)**
# Trigger deployment Fri Feb  6 11:25:29 PST 2026
