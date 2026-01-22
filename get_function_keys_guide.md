# Getting Function App Keys for Application Insights Tests

## Method 1: Azure Portal (Easiest)

1. **Go to Azure Portal → petclinic-apm-function-app2**
2. **Left sidebar → App keys**
3. **Copy the "default" key under "Host keys"**
   - This key works for all functions in the app
   - Format: `https://your-function-app.azurewebsites.net/api/appointments?code=YOUR_KEY_HERE`

## Method 2: Per-Function Keys (More Secure)

1. **Go to Azure Portal → petclinic-apm-function-app2**
2. **Left sidebar → Functions**
3. **Click on each function (GetAllAppointments, CreateAppointment, DeleteAppointment)**
4. **Click "Function Keys" → Copy the "default" key**

## Function URLs with Keys:

### GetAllAppointments (GET)
```
https://petclinic-apm-function-app2.azurewebsites.net/api/appointments?code=YOUR_FUNCTION_KEY
```

### CreateAppointment (POST)  
```
https://petclinic-apm-function-app2.azurewebsites.net/api/appointments?code=YOUR_FUNCTION_KEY
```

### DeleteAppointment (DELETE)
```
https://petclinic-apm-function-app2.azurewebsites.net/api/appointments/{id}?code=YOUR_FUNCTION_KEY
```

## Sample POST Body for CreateAppointment:
```json
{
  "patient_name": "Test Patient",
  "patient_email": "test@example.com",
  "patient_phone": "+1-555-123-4567",
  "doctor_name": "Dr. Test",
  "appointment_date": "2026-02-15",
  "appointment_time": "14:30",
  "appointment_type": "Traffic Generation Test"
}
```

---
**Next:** Once you have the keys, we'll create the Application Insights Availability Tests.
