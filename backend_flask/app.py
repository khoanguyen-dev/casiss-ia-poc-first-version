from flask import Flask
from flask_cors import CORS
from routes.annuaire import annuaire_bp
from routes.evenement import evenement_bp
from routes.navisante import navisante_bp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(annuaire_bp, url_prefix='/annuaire')
app.register_blueprint(evenement_bp, url_prefix='/evenement')
app.register_blueprint(navisante_bp, url_prefix='/navisante')

if __name__ == '__main__':
    app.run(debug=True)
    