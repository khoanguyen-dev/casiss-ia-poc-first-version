import React, { useState, memo } from "react";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const AnnuaireTable = memo(({ entries, handleUpdateAnnuaire, isProcessingComplete }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKey, setSearchKey] = useState("");
  const [searchField, setSearchField] = useState("nom");

  const entriesPerPage = 7;
  const validEntries = Array.isArray(entries) ? entries : [];
  const totalPages = Math.ceil(
    validEntries.filter((entry) =>
      searchKey
        ? String(entry[searchField] || "")
            .toLowerCase()
            .includes(searchKey.toLowerCase())
        : true
    ).length / entriesPerPage
  );

  const handleSearch = (e) => {
    setSearchKey(e.target.value);
    setCurrentPage(1); // Reset to the first page on search
  };

  const handleFieldChange = (e) => {
    setSearchField(e.target.value);
    setCurrentPage(1); // Reset to the first page on field change
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  // Filter and paginate entries
  const filteredEntries = entries.filter((entry) =>
    searchKey
      ? String(entry[searchField] || "")
          .toLowerCase()
          .includes(searchKey.toLowerCase())
      : true
  );
  const paginatedEntries = filteredEntries.slice(
    (currentPage - 1) * entriesPerPage,
    currentPage * entriesPerPage
  );

  return (
    <section className="mt-4">
      {/* Search Controls */}
      <div className="d-flex align-items-center mb-3">
        <input
          type="text"
          className="form-control me-2"
          placeholder="Rechercher..."
          value={searchKey}
          onChange={handleSearch}
        />
        <select
          className="form-select"
          value={searchField}
          onChange={handleFieldChange}
        >
          <option value="nom">Nom</option>
          <option value="prenom">Prénom</option>
          <option value="telephone">Téléphone</option>
          <option value="courriel">Courriel</option>
          <option value="localite">Localité</option>
        </select>
      </div>

      {/* Scrollable Table */}
      <div style={{ overflowX: "auto" }}>
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr>
              <th style={{ minWidth: "140px" }}></th>
              <th style={{ minWidth: "40px" }}>ID</th>
              <th style={{ minWidth: "90px" }}>No EAN</th>
              <th style={{ minWidth: "100px" }}>Type</th>
              <th style={{ minWidth: "150px" }}>Type de Fournisseur</th>
              <th style={{ minWidth: "150px" }}>Nom</th>
              <th style={{ minWidth: "150px" }}>Prénom</th>
              <th style={{ minWidth: "120px" }}>Acronyme</th>
              <th style={{ minWidth: "150px" }}>Téléphone</th>
              <th style={{ minWidth: "150px" }}>Portable</th>
              <th style={{ minWidth: "200px" }}>Courriel</th>
              <th style={{ minWidth: "200px" }}>Site Web</th>
              <th style={{ minWidth: "200px" }}>Lien Org</th>
              <th style={{ minWidth: "150px" }}>Organisation</th>
              <th style={{ minWidth: "200px" }}>Rôle/Activité/Spécialité</th>
              <th style={{ minWidth: "100px" }}>Médecin</th>
              <th style={{ minWidth: "150px" }}>Médecin Intra-Hospitalier</th>
              <th style={{ minWidth: "50px" }}>Lu</th>
              <th style={{ minWidth: "50px" }}>Ma</th>
              <th style={{ minWidth: "50px" }}>Me</th>
              <th style={{ minWidth: "50px" }}>Je</th>
              <th style={{ minWidth: "50px" }}>Ve</th>
              <th style={{ minWidth: "50px" }}>Sa</th>
              <th style={{ minWidth: "50px" }}>Di</th>
              <th style={{ minWidth: "200px" }}>Tags</th>
              <th style={{ minWidth: "200px" }}>Sélection</th>
              <th style={{ minWidth: "250px" }}>Commentaire</th>
              <th style={{ minWidth: "200px" }}>Voie</th>
              <th style={{ minWidth: "100px" }}>Numéro</th>
              <th style={{ minWidth: "200px" }}>Complément</th>
              <th style={{ minWidth: "100px" }}>NPA</th>
              <th style={{ minWidth: "150px" }}>Localité</th>
              <th style={{ minWidth: "150px" }}>Pays</th>
              <th style={{ minWidth: "150px" }}>Coord Geo Nord</th>
              <th style={{ minWidth: "150px" }}>Coord Geo Est</th>
              <th style={{ minWidth: "150px" }}>Longitude</th>
              <th style={{ minWidth: "150px" }}>Latitude</th>
              <th style={{ minWidth: "200px" }}>Date Dernière Modification</th>
            </tr>
          </thead>
          <tbody>
          {paginatedEntries.length > 0 ? (
              paginatedEntries.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    <button
                      className="btn btn-warning"
                      onClick={() => handleUpdateAnnuaire(entry.id, entry.nom, entry.prenom)}
                      disabled={!isProcessingComplete}
                    >
                      Mise à jour
                    </button>
                  </td>
                  <td>{entry.id}</td>
                  <td>{entry.no_ean}</td>
                  <td>{entry.type}</td>
                  <td>{entry.type_de_fournisseur}</td>
                  <td>{entry.nom}</td>
                  <td>{entry.prenom}</td>
                  <td>{entry.acronyme}</td>
                  <td>{entry.telephone}</td>
                  <td>{entry.portable}</td>
                  <td>{entry.courriel}</td>
                  <td>{entry.site_web}</td>
                  <td>{entry.lien_org}</td>
                  <td>{entry.organisation}</td>
                  <td>{entry.role_activite_specialite}</td>
                  <td>{entry.medecin ? "Oui" : "Non"}</td>
                  <td>{entry.medecin_intra_hospitalier ? "Oui" : "Non"}</td>
                  <td>{entry.lu ? "Oui" : "Non"}</td>
                  <td>{entry.ma ? "Oui" : "Non"}</td>
                  <td>{entry.me ? "Oui" : "Non"}</td>
                  <td>{entry.je ? "Oui" : "Non"}</td>
                  <td>{entry.ve ? "Oui" : "Non"}</td>
                  <td>{entry.sa ? "Oui" : "Non"}</td>
                  <td>{entry.di ? "Oui" : "Non"}</td>
                  <td>{entry.tags}</td>
                  <td>{entry.selection}</td>
                  <td>{entry.commentaire}</td>
                  <td>{entry.voie}</td>
                  <td>{entry.numero}</td>
                  <td>{entry.complement}</td>
                  <td>{entry.npa}</td>
                  <td>{entry.localite}</td>
                  <td>{entry.pays}</td>
                  <td>{entry.coord_geo_nord}</td>
                  <td>{entry.coord_geo_est}</td>
                  <td>{entry.longitude}</td>
                  <td>{entry.latitude}</td>
                  <td style={{ whiteSpace: "nowrap", minWidth: "150px" }}>
                    {entry.date_derniere_modification}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="38" className="text-center">
                  Aucune entrée trouvée.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="d-flex justify-content-between align-items-center">
        <button
          className="btn btn-secondary"
          onClick={handlePreviousPage}
          disabled={currentPage === 1}
        >
          Précédent
        </button>
        <span>
          Page {currentPage} sur {totalPages}
        </span>
        <button
          className="btn btn-secondary"
          onClick={handleNextPage}
          disabled={currentPage === totalPages}
        >
          Suivant
        </button>
      </div>
    </section>
  );
});

export default AnnuaireTable;
