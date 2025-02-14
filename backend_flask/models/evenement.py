from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

class EvenementEntry(BaseModel):
    """Model representing an entry for the Evenement database."""
    id: Optional[int] = None 
    nom_evenement: str  # Name of the event, required
    titre_evenement: Optional[str] = None  # Event title, optional
    date_debut: Optional[str] = None  # Event start date
    date_fin: Optional[str] = None  # Event end date
    horaire_debut: Optional[str] = None  # Event start time optional
    horaire_fin: Optional[str] = None  # Event end time optional
    public_cible: Optional[str] = None # Target population optional
    texte_libre: Optional[str] = None  # Free text for additional information
    court_descriptif: Optional[str] = None  # Short description
    numero_partenaire: Optional[str] = None  # Partner number, optional
    nom_partenaire: Optional[str] = None  # Partner name, optional
    partenaire_de_la_selection: Optional[str] = None  # Selected partner text, optional
    sites_originaux: Optional[str] = None  # Original sites, optional
    date_creation: Optional[str] = None  # Record creation date
    mode_creation: Optional[str] = None  # Mode of creation
    mode_modification: Optional[str] = None  # Mode of modification
    id_dernier_modificateur: Optional[str] = None  # ID of the last modifier
    date_de_peremption: Optional[str] = None  # Expiration date

    @field_validator(
        "horaire_debut", "horaire_fin", "date_creation", "date_de_peremption", 
        "numero_partenaire", "id_dernier_modificateur",
        mode="before"
    )
    @classmethod
    def convert_numero(cls, v):
        """Ensure numero is always a string."""
        if v is None:
            return v
        return str(v)
    
class EvenementEntries(BaseModel):
    """Model representing multiple entries for the Evenement database."""
    entries: list[EvenementEntry]
