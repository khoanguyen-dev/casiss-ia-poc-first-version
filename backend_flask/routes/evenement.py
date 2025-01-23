from flask import Blueprint
from services.database import fetch_table_entries, add_entry, replace_entry, process_input

evenement_bp = Blueprint('evenement', __name__)

@evenement_bp.route('/get', methods=['GET'])
def get_evenement_entries():
    return fetch_table_entries('evenement')

@evenement_bp.route('/process', methods=['POST'])
def process_annuaire_input():
    return process_input("evenement")

@evenement_bp.route('/add', methods=['POST'])
def add_evenement():
    return add_entry('evenement')

@evenement_bp.route('/replace', methods=['PUT'])
def replace_evenement():
    return replace_entry('evenement')
