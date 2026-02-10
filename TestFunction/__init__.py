"""
Minimal test function to debug import issues
"""
import logging
import json
import azure.functions as func

# Import telemetry for trace context
try:
    from shared_code.telemetry import trace_context_manager
except ImportError:
    trace_context_manager = None


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Test function with no imports"""
    logging.info("=== TEST FUNCTION WORKING ===")
    
    # Use trace_context_manager to ensure all Azure SDK calls inherit APIM trace context
    with trace_context_manager(req, "TestFunction"):
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
