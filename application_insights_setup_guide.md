# Application Insights Availability Tests Setup Guide

## Overview
This guide will help you set up 3 Availability Tests in Application Insights to generate continuous traffic to your APIs every minute.

## Prerequisites
- ✅ Application Insights connected to your Function App
- ✅ Function App keys obtained (see get_function_keys_guide.md)

---

## Test 1: GetAllAppointments Traffic Generator

### Steps:
1. **Go to Azure Portal → Application Insights → Availability**
2. **Click "Add Classic test"**
3. **Configure:**
   - **Test name:** `GetAllAppointments-Traffic-1min`
   - **Test type:** URL ping test
   - **URL:** `https://petclinic-apm-function-app2.azurewebsites.net/api/appointments?code=YOUR_HOST_KEY`
   - **HTTP method:** GET
   - **Parse dependent requests:** Unchecked
   - **Enable retries:** Checked
   - **Test frequency:** 1 minute
   - **Test locations:** Select 5 locations (US East, US West, Europe West, Asia East, Australia East)

4. **Success criteria:**
   - **HTTP response code:** Equals 200
   - **Content contains:** `"success": true` or `"data"`

5. **Click "Create"**

---

## Test 2: CreateAppointment Traffic Generator

### Steps:
1. **Go to Azure Portal → Application Insights → Availability**
2. **Click "Add Classic test"**
3. **Configure:**
   - **Test name:** `CreateAppointment-Traffic-1min`
   - **Test type:** URL ping test
   - **URL:** `https://petclinic-apm-function-app2.azurewebsites.net/api/appointments?code=YOUR_HOST_KEY`
   - **HTTP method:** POST
   - **Headers:** Click "Add header"
     - Name: `Content-Type`
     - Value: `application/json`
   - **Body:** 
```json
{
  "patient_name": "AI Test Patient",
  "patient_email": "ai.test@example.com",
  "patient_phone": "+1-555-000-0001",
  "doctor_name": "Dr. AI Test",
  "appointment_date": "2026-02-20",
  "appointment_time": "10:00",
  "appointment_type": "Application Insights Traffic Test"
}
```
   - **Test frequency:** 1 minute
   - **Test locations:** Select same 5 locations as Test 1

4. **Success criteria:**
   - **HTTP response code:** Equals 201
   - **Content contains:** `"success": true`

5. **Click "Create"**

---

## Test 3: Cleanup Test (Every 5 Minutes)

### Option A: Simple URL Ping for Health Check
1. **Go to Azure Portal → Application Insights → Availability**
2. **Click "Add Classic test"**
3. **Configure:**
   - **Test name:** `API-Health-Check-5min`
   - **Test type:** URL ping test
   - **URL:** `https://petclinic-apm-function-app2.azurewebsites.net/api/debug?code=YOUR_HOST_KEY`
   - **HTTP method:** GET
   - **Test frequency:** 5 minutes
   - **Test locations:** Select 3 locations

4. **Success criteria:**
   - **HTTP response code:** Equals 200
   - **Content contains:** `"status": "SUCCESS"`

---

## Expected Results

### Traffic Generated:
- **GetAllAppointments:** 5 locations × 60 calls/hour = 300 requests/hour
- **CreateAppointment:** 5 locations × 60 calls/hour = 300 requests/hour  
- **Health Check:** 3 locations × 12 calls/hour = 36 requests/hour
- **Total:** ~636 API calls per hour

### What You'll See:
1. **Function App Metrics:** Increased request count and execution count
2. **Application Insights:** 
   - Traffic patterns in Application Map
   - Response times in Performance blade
   - Success rates in Availability blade
3. **Cosmos DB:** New appointments being created continuously

---

## Monitoring Your Traffic

### View Traffic in Application Insights:
1. **Application Insights → Application Map** - Visual traffic flow
2. **Application Insights → Performance** - Response times and throughput
3. **Application Insights → Availability** - Success rates of your tests
4. **Application Insights → Live Metrics** - Real-time traffic (optional)

### View Function App Metrics:
1. **Function App → Overview** - Request count and execution count
2. **Function App → Functions → [Function Name] → Monitor** - Individual function metrics

---

## Notes:
- Tests will start immediately after creation
- Each test runs independently from 5 different global locations
- No alerts configured (as requested)
- Traffic will appear as real user traffic in all Azure dashboards
- Data will accumulate in Cosmos DB - monitor storage usage

## Troubleshooting:
- If tests fail: Check function keys are correct
- If no traffic: Verify test frequency and locations
- If high latency: Consider reducing test locations
