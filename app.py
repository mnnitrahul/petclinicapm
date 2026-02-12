import os
from flask import Flask
from azure.cosmos import CosmosClient

app = Flask(__name__)

@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask Web App!'}

@app.route('/')
def health():
    return {'status': 'healthy'}

@app.route('/api/appointments')
def get_appointments():
    try:
        endpoint = os.environ.get('COSMOS_DB_ENDPOINT', 'https://apmwebapp-server.documents.azure.com:443/')
        key = os.environ.get('COSMOS_DB_KEY')
        if not key:
            return {'error': 'COSMOS_DB_KEY not configured'}, 500
        
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(os.environ.get('COSMOS_DB_DATABASE', 'petclinic'))
        container = database.get_container_client(os.environ.get('COSMOS_DB_CONTAINER', 'appointments'))
        
        items = list(container.query_items('SELECT * FROM c', enable_cross_partition_query=True, max_item_count=10))
        return {'appointments': items}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run()
