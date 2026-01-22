"""
Simple Hello World function to test if Azure Functions are working at all
"""
import azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Simple Hello World function with visible debug info"""
    
    # Use logging (better for Azure Functions)
    logging.info("=== HELLO WORLD FUNCTION STARTED ===")
    logging.info(f"Request method: {req.method}")
    logging.info(f"Request URL: {req.url}")
    
    # Collect debug info to return in response
    debug_info = [
        "✅ Azure Functions runtime is WORKING!",
        f"✅ Request method: {req.method}",
        f"✅ Request URL: {req.url}",
        "✅ Function executed successfully",
        "✅ This proves your functions can be created and called"
    ]
    
    response = {
        "message": "🎉 Hello World from Azure Functions!",
        "status": "SUCCESS", 
        "debug_info": debug_info,
        "conclusions": [
            "Azure Functions deployment is working",
            "Function creation is working", 
            "The 500 errors in other functions are likely import/environment issues",
            "Basic Python and JSON functionality works fine"
        ]
    }
    
    logging.info("=== HELLO WORLD FUNCTION SUCCESS ===")
    
    return func.HttpResponse(
        json.dumps(response, indent=2),
        status_code=200,
        mimetype="application/json"
    )
