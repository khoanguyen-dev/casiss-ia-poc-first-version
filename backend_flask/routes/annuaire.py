from flask import Blueprint
from services.database import fetch_table_entries, add_entry, replace_entry, update_annuaire, resolve_conflicts, process_input

annuaire_bp = Blueprint('annuaire', __name__)

@annuaire_bp.route('/get', methods=['GET'])
def get_annuaire_entries():
    return fetch_table_entries('annuaire')

@annuaire_bp.route('/process', methods=['POST'])
def process_annuaire_input():
    return process_input("annuaire")

@annuaire_bp.route('/add', methods=['POST'])
def add_annuaire():
    return add_entry('annuaire')

@annuaire_bp.route('/replace', methods=['PUT'])
def replace_annuaire():
    return replace_entry('annuaire')

@annuaire_bp.route('/update', methods=['POST'])
def update_annuaire_entries():
    return update_annuaire()

@annuaire_bp.route('/resolve-conflicts', methods=['POST'])
def resolve_annuaire_conflicts():
    return resolve_conflicts()
