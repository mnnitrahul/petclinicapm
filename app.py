import os
import logging
from flask import Flask
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conn_string = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
logger.info(f"APPLICATIONINSIGHTS_CONNECTION_STRING present: {bool(conn_string)}")

if conn_string:
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        configure_azure_monitor()
        logger.info("Azure Monitor configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Azure Monitor: {e}")

app = Flask(__name__)

# Instrument Flask after app is created
if conn_string:
    try:
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumentation enabled")
    except Exception as e:
        logger.error(f"Failed to instrument Flask: {e}")

@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask Web App!'}

@app.route('/')
def health():
    return {'status': 'healthy'}

@app.route('/api/appointments')
def get_appointments():
    try:
        connection_string = os.environ.get('AZURE_COSMOS_CONNECTIONSTRING')
        if not connection_string:
            return {'error': 'AZURE_COSMOS_CONNECTIONSTRING not configured'}, 500
        
        client = MongoClient(connection_string)
        db = client[os.environ.get('COSMOS_DB_DATABASE', 'petclinic')]
        collection = db[os.environ.get('COSMOS_DB_CONTAINER', 'appointments')]
        
        items = list(collection.find({}, {'_id': 0}).limit(10))
        return {'appointments': items}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run()
