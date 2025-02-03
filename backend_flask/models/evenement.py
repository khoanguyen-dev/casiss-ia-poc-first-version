from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

class EvenementEntry(BaseModel):
    """Model representing an entry for the Evenement database."""
    id: Optional[int] = None 
    nom_evenement: Optional[str]  # Name of the event, required
    titre_evenement: Optional[str] = None  # Event title, optional
    horaire_debut: Optional[datetime] = None  # Event start timestamp
    horaire_fin: Optional[datetime] = None  # Event end timestamp
    texte_libre: Optional[str] = None  # Free text for additional information
    court_descriptif: Optional[str] = None  # Short description
    numero_partenaire: Optional[int] = None  # Partner number, optional
    nom_partenaire: Optional[str] = None  # Partner name, optional
    partenaire_de_la_selection: Optional[str] = None  # Selected partner text, optional
    sites_originaux: Optional[str] = None  # Original sites, optional
    date_creation: Optional[date] = None  # Record creation date
    mode_creation: Optional[str] = None  # Mode of creation
    mode_modification: Optional[str] = None  # Mode of modification
    id_dernier_modificateur: Optional[int] = None  # ID of the last modifier
    date_de_peremption: Optional[datetime] = None  # Expiration date

    @field_validator("horaire_debut", "horaire_fin", "date_creation", "date_de_peremption", mode="before")
    @classmethod
    def convert_empty_string_to_none(cls, v):
        """Convert empty string values to None to avoid validation errors."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    class Config:
        from_attributes = True

class EvenementEntries(BaseModel):
    """Model representing multiple entries for the Evenement database."""
    entries: list[EvenementEntry]
