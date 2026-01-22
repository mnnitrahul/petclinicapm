"""
Minimal test function to debug import issues
"""
import logging
import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test function with no imports"""
    logging.info("=== TEST FUNCTION WORKING ===")
    
    response = {
        "success": True,
        "message": "Test function is working - no import issues",
        "request_method": req.method,
        "request_url": str(req.url)
    }
    
    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )
