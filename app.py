from flask import Flask

app = Flask(__name__)

@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask Web App!'}

@app.route('/')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run()
