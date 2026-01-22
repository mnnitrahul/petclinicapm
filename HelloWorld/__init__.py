"""
Simple Hello World function to test if Azure Functions are working at all
"""
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simple Hello World function"""
    print("=== HELLO WORLD FUNCTION STARTED ===")
    print(f"Request method: {req.method}")
    print(f"Request URL: {req.url}")
    print("=== HELLO WORLD FUNCTION WORKING ===")
    
    response = {
        "message": "Hello World from Azure Functions!",
        "status": "SUCCESS",
        "method": req.method,
        "timestamp": "2026-01-22"
    }
    
    print(f"Response: {response}")
    print("=== HELLO WORLD FUNCTION END ===")
    
    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )
