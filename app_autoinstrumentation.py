import os
from flask import Flask
from pymongo import MongoClient

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
        connection_string = os.environ.get('AZURE_COSMOS_CONNECTIONSTRING')
        if not connection_string:
            return {'error': 'AZURE_COSMOS_CONNECTIONSTRING not configured'}, 500
        
        client = MongoClient(connection_string)
        db = client.get_default_database()
        collection = db[os.environ.get('COSMOS_DB_CONTAINER', 'appointments')]
        
        items = list(collection.find({}, {'_id': 0}).limit(10))
        return {'appointments': items}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run()
