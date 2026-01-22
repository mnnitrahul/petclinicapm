"""
Debug function to print all environment variables and test Cosmos DB connection
"""
import azure.functions as func
import json
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Debug function with environment variables and Cosmos DB test"""
    print("=== DEBUG ENVIRONMENT FUNCTION START ===")
    print(f"Request method: {req.method}")
    print(f"Request URL: {req.url}")
    
    # Print ALL environment variables
    print("\n=== ALL ENVIRONMENT VARIABLES ===")
    env_vars = {}
    for key, value in os.environ.items():
        # Mask sensitive values but show they exist
        if 'key' in key.lower() or 'secret' in key.lower() or 'password' in key.lower():
            masked_value = f"***MASKED*** (length: {len(value)})"
            env_vars[key] = masked_value
            print(f"{key}: {masked_value}")
        else:
            env_vars[key] = value
            print(f"{key}: {value}")
    
    print(f"\nTotal environment variables: {len(env_vars)}")
    
    # Check specific Cosmos DB variables
    print("\n=== COSMOS DB ENVIRONMENT VARIABLES ===")
    cosmos_endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
    cosmos_key = os.environ.get("COSMOS_DB_KEY")
    cosmos_database = os.environ.get("COSMOS_DB_DATABASE", "petclinic")
    cosmos_container = os.environ.get("COSMOS_DB_CONTAINER", "appointments")
    
    print(f"COSMOS_DB_ENDPOINT: {cosmos_endpoint}")
    print(f"COSMOS_DB_KEY present: {bool(cosmos_key)}")
    print(f"COSMOS_DB_DATABASE: {cosmos_database}")
    print(f"COSMOS_DB_CONTAINER: {cosmos_container}")
    
    # Test Cosmos DB import and connection
    cosmos_status = {}
    print("\n=== COSMOS DB CONNECTION TEST ===")
    
    try:
        print("Attempting to import azure.cosmos...")
        from azure.cosmos import CosmosClient, PartitionKey
        print("✅ azure.cosmos import successful")
        cosmos_status["import"] = "SUCCESS"
        
        if cosmos_endpoint and cosmos_key:
            print("Attempting to create CosmosClient...")
            client = CosmosClient(cosmos_endpoint, cosmos_key)
            print("✅ CosmosClient created successfully")
            cosmos_status["client_creation"] = "SUCCESS"
            
            print("Attempting to list databases...")
            databases = list(client.list_databases())
            print(f"✅ Successfully listed {len(databases)} databases")
            cosmos_status["database_list"] = f"SUCCESS - {len(databases)} databases"
            
            # Print database names
            for db in databases:
                print(f"  Database: {db['id']}")
                
        else:
            print("❌ Missing Cosmos DB credentials")
            cosmos_status["credentials"] = "MISSING"
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        cosmos_status["import"] = f"FAILED - {e}"
    except Exception as e:
        print(f"❌ Connection error: {e}")
        cosmos_status["connection"] = f"FAILED - {e}"
    
    # Prepare comprehensive response with ALL debug info visible
    response = {
        "message": "🔍 Debug Environment function completed",
        "status": "SUCCESS",
        "cosmos_status": cosmos_status,
        "cosmos_details": {
            "endpoint": cosmos_endpoint if cosmos_endpoint else "❌ MISSING",
            "key_present": "✅ YES" if cosmos_key else "❌ NO",
            "key_length": len(cosmos_key) if cosmos_key else 0,
            "database": cosmos_database,
            "container": cosmos_container
        },
        "environment_summary": {
            "total_env_vars": len(env_vars),
            "cosmos_endpoint_present": bool(cosmos_endpoint),
            "cosmos_key_present": bool(cosmos_key)
        },
        "key_environment_variables": {
            key: env_vars[key] for key in env_vars 
            if key.startswith('COSMOS_') or key.startswith('AZURE_') or key.startswith('FUNCTIONS_')
        },
        "diagnosis": [
            "✅ Azure Functions runtime working" if True else "❌ Runtime issue",
            "✅ Environment variables accessible" if env_vars else "❌ No env vars",
            "✅ Cosmos DB endpoint configured" if cosmos_endpoint else "❌ Missing COSMOS_DB_ENDPOINT",
            "✅ Cosmos DB key configured" if cosmos_key else "❌ Missing COSMOS_DB_KEY",
            "✅ azure.cosmos package available" if cosmos_status.get("import") == "SUCCESS" else "❌ azure.cosmos package missing"
        ]
    }
    
    print(f"\n=== FINAL RESPONSE ===")
    print(json.dumps(response, indent=2))
    print("=== DEBUG ENVIRONMENT FUNCTION END ===")
    
    return func.HttpResponse(
        json.dumps(response, indent=2),
        status_code=200,
        mimetype="application/json"
    )
