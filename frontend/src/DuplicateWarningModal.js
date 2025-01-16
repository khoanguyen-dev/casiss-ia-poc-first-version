import React, { useState, useEffect, useMemo } from "react";

function DuplicateWarningModal({ duplicate, onUpdate, onReplace, onAdd, onCancel, onNext }) {
  const TABLE_FIELDS = useMemo(
    () => duplicate?.new_entry?.hasOwnProperty("nom_evenement")
    ? [
        "nom_evenement",
        "titre_evenement",
        "date_debut",
        "date_fin",
        "horaire_debut",
        "horaire_fin",
        "texte_libre",
        "court_descriptif",
        "numero_partenaire",
        "nom_partenaire",
        "partenaire_de_la_selection",
        "sites_originaux",
        "date_creation",
        "mode_creation",
        "mode_modification",
        "id_dernier_modificateur",
        "date_de_peremption",
      ]
    : [
        "no_ean",
        "type",
        "type_de_fournisseur",
        "nom",
        "prenom",
        "acronyme",
        "telephone",
        "portable",
        "courriel",
        "site_web",
        "lien_org",
        "organisation",
        "role_activite_specialite",
        "medecin",
        "medecin_intra_hospitalier",
        "lu",
        "ma",
        "me",
        "je",
        "ve",
        "sa",
        "di",
        "tags",
        "selection",
        "commentaire",
        "voie",
        "numero",
        "complement",
        "npa",
        "localite",
        "pays",
        "coord_geo_nord",
        "coord_geo_est",
        "longitude",
        "latitude",
      ],
    [duplicate]
  );

  const [editedEntry, setEditedEntry] = useState({});
  const [selectedExistingEntry, setSelectedExistingEntry] = useState(null);

  useEffect(() => {
    if (duplicate) {
      const newEntryData = TABLE_FIELDS.reduce(
        (acc, field) => ({
          ...acc,
          [field]: duplicate.new_entry[field] || "",
        }),
        {}
      );
      setEditedEntry(newEntryData);
      setSelectedExistingEntry(null);
    }
  }, [duplicate, TABLE_FIELDS]);

  const handleFieldChange = (field, value) => {
    setEditedEntry((prev) => ({ ...prev, [field]: value }));
  };

  const handleSelectExistingEntry = (entry) => {
    console.log("Selected existing entry:", entry); // Debugging log
    setSelectedExistingEntry(entry);
    setEditedEntry((prev) => ({ ...prev, existing_id: entry.id }));
  };

  const handleAddAndNext = async () => {
    console.log("New entry being added:", editedEntry); // Debugging log
    await onAdd({ new_entry: editedEntry }); // Pass `new_entry` correctly
    onNext();
  };

  const handleReplaceAndNext = async () => {
    if (!selectedExistingEntry) {
      alert("Veuillez sélectionner une entrée existante à remplacer.");
      return;
    }
  
    const payload = {
      new_entry: editedEntry, // Ensure the new entry data is passed
    };
  
    await onReplace(payload);
    onNext();
  };

  return (
    <div className="modal show d-block">
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header bg-danger text-white">
            <h5 className="modal-title">Doublon détecté</h5>
            <button className="btn-close text-white" onClick={onCancel}></button>
          </div>
          <div className="modal-body">
            <p className="text-danger">
              Résolvez le doublon en remplissant tous les champs, en ajoutant comme nouvelle entrée ou en remplaçant une entrée existante.
            </p>

            <h6>Nouvelle entrée :</h6>
            <form>
              {TABLE_FIELDS.map((field) => (
                <div className="mb-3" key={field}>
                  <label className="form-label">
                    {field.replace(/_/g, " ").toUpperCase()}
                  </label>
                  <input
                    type={field.includes("date") ? "date" : "text"}
                    value={editedEntry[field] || ""}
                    onChange={(e) => handleFieldChange(field, e.target.value)}
                    className="form-control"
                  />
                </div>
              ))}
            </form>

            <h6>Entrées existantes dans la base de données :</h6>
            {duplicate?.existing_entries.map((existing, idx) => (
              <div
                key={idx}
                className={`border p-2 mb-2 ${
                  selectedExistingEntry?.id === existing.id
                    ? "border-primary bg-light"
                    : "border-secondary"
                }`}
                onClick={() => handleSelectExistingEntry(existing)}
                style={{ cursor: "pointer" }}
              >
                <strong>ID {existing.id} :</strong>
                <pre>{JSON.stringify(existing, null, 2)}</pre>
              </div>
            ))}
          </div>
          <div className="modal-footer">
            <button className="btn btn-success" onClick={handleAddAndNext}>
              Ajouter comme nouvelle entrée
            </button>
            <button className="btn btn-warning" onClick={handleReplaceAndNext}>
              Remplacer l'entrée sélectionnée
            </button>
            <button className="btn btn-info" onClick={onNext}>
              Passer au doublon suivant
            </button>
            <button className="btn btn-secondary" onClick={onCancel}>
              Annuler
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DuplicateWarningModal;
