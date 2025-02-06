from pydantic import BaseModel, field_validator
from typing import Optional

class AnnuaireEntry(BaseModel):
    """Model representing an entry for the Annuaire database."""
    id: Optional[int] = None
    no_ean: Optional[str] = None
    type: Optional[str] = None  # Personne/Organization
    type_de_fournisseur: Optional[str] = None
    nom: str = None
    prenom: str = None
    acronyme: Optional[str] = None
    telephone: Optional[str] = None
    portable: Optional[str] = None
    courriel: Optional[str] = None
    site_web: Optional[str] = None
    lien_org: Optional[str] = None
    organisation: Optional[str] = None
    role_activite_specialite: Optional[str] = None
    medecin: Optional[bool] = None
    medecin_intra_hospitalier: Optional[bool] = None
    lu: Optional[bool] = None
    ma: Optional[bool] = None
    me: Optional[bool] = None
    je: Optional[bool] = None
    ve: Optional[bool] = None
    sa: Optional[bool] = None
    di: Optional[bool] = None
    tags: Optional[str] = None
    selection: Optional[str] = None
    commentaire: Optional[str] = None
    voie: Optional[str] = None
    numero: Optional[str] = None
    complement: Optional[str] = None
    npa: Optional[str] = None
    localite: Optional[str] = None
    pays: Optional[str] = None
    coord_geo_nord: Optional[str] = None
    coord_geo_est: Optional[str] = None
    longitude: Optional[str] = None
    latitude: Optional[str] = None

    @field_validator("numero", "npa", mode="before")
    @classmethod
    def convert_numero(cls, v):
        """Ensure numero is always a string."""
        if v is None:
            return v
        return str(v)

    class Config:
        from_attributes = True


class AnnuaireEntries(BaseModel):
    """Model representing multiple entries for the Annuaire database."""
    entries: list[AnnuaireEntry]
