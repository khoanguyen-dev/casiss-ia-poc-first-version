import React, { useState, memo } from "react";

const EvenementTable = memo(({ evenements }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKey, setSearchKey] = useState("");
  const [searchField, setSearchField] = useState("nom_evenement");

  const entriesPerPage = 10;
  const totalPages = Math.ceil(
    evenements.filter((evenement) =>
      searchKey
        ? String(evenement[searchField] || "")
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
  const filteredEvenements = evenements.filter((evenement) =>
    searchKey
      ? String(evenement[searchField] || "")
          .toLowerCase()
          .includes(searchKey.toLowerCase())
      : true
  );
  const paginatedEvenements = filteredEvenements.slice(
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
          <option value="nom_evenement">Nom de l'Événement</option>
          <option value="titre_evenement">Titre</option>
          <option value="date_debut">Date de Début</option>
          <option value="nom_partenaire">Nom Partenaire</option>
          <option value="localite">Localité</option>
        </select>
      </div>

      {/* Scrollable Table */}
      <div style={{ overflowX: "auto" }}>
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr>
              <th style={{ minWidth: "100px" }}>ID</th>
              <th style={{ minWidth: "200px" }}>Nom de l'Événement</th>
              <th style={{ minWidth: "200px" }}>Titre</th>
              <th style={{ minWidth: "150px" }}>Date de Début</th>
              <th style={{ minWidth: "150px" }}>Date de Fin</th>
              <th style={{ minWidth: "200px" }}>Horaire Début</th>
              <th style={{ minWidth: "200px" }}>Horaire Fin</th>
              <th style={{ minWidth: "300px" }}>Texte Libre</th>
              <th style={{ minWidth: "300px" }}>Court Descriptif</th>
              <th style={{ minWidth: "150px" }}>Numéro Partenaire</th>
              <th style={{ minWidth: "200px" }}>Nom Partenaire</th>
              <th style={{ minWidth: "250px" }}>
                Partenaire de la Sélection
              </th>
              <th style={{ minWidth: "250px" }}>Sites Originaux</th>
              <th style={{ minWidth: "150px" }}>Date de Création</th>
              <th style={{ minWidth: "150px" }}>Mode de Création</th>
              <th style={{ minWidth: "200px" }}>
                Date de Dernière Modification
              </th>
              <th style={{ minWidth: "150px" }}>Mode de Modification</th>
              <th style={{ minWidth: "200px" }}>ID Dernier Modificateur</th>
              <th style={{ minWidth: "200px" }}>Date de Péremption</th>
            </tr>
          </thead>
          <tbody>
            {paginatedEvenements.length > 0 ? (
              paginatedEvenements.map((evenement) => (
                <tr key={evenement.id}>
                  <td>{evenement.id}</td>
                  <td>{evenement.nom_evenement}</td>
                  <td>{evenement.titre_evenement}</td>
                  <td>{evenement.date_debut}</td>
                  <td>{evenement.date_fin}</td>
                  <td>{evenement.horaire_debut}</td>
                  <td>{evenement.horaire_fin}</td>
                  <td>{evenement.texte_libre}</td>
                  <td>{evenement.court_descriptif}</td>
                  <td>{evenement.numero_partenaire}</td>
                  <td>{evenement.nom_partenaire}</td>
                  <td>{evenement.partenaire_de_la_selection}</td>
                  <td>{evenement.sites_originaux}</td>
                  <td>{evenement.date_creation}</td>
                  <td>{evenement.mode_creation}</td>
                  <td>{evenement.date_derniere_modification}</td>
                  <td>{evenement.mode_modification}</td>
                  <td>{evenement.id_dernier_modificateur}</td>
                  <td>{evenement.date_de_peremption}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="19" className="text-center">
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

export default EvenementTable;
