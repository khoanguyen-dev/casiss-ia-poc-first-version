import React, { useState, memo } from "react";

const NavisanteTable = memo(({ navisanteEntries }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchKey, setSearchKey] = useState("");
  const [searchField, setSearchField] = useState("source");

  const entriesPerPage = 10;
  const totalPages = Math.ceil(
    navisanteEntries.filter((entry) =>
      searchKey
        ? String(entry[searchField] || "")
            .toLowerCase()
            .includes(searchKey.toLowerCase())
        : true
    ).length / entriesPerPage
  );

  const handleSearch = (e) => {
    setSearchKey(e.target.value);
    setCurrentPage(1);
  };

  const handleFieldChange = (e) => {
    setSearchField(e.target.value);
    setCurrentPage(1);
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const filteredEntries = navisanteEntries.filter((entry) =>
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
          <option value="source">Source</option>
          <option value="keywords">Mots-Clés</option>
          <option value="content">Contenu</option>
        </select>
      </div>

      {/* Scrollable Table */}
      <div style={{ overflowX: "auto" }}>
        <table className="table table-striped table-bordered">
          <thead className="table-dark">
            <tr>
              <th style={{ minWidth: "200px" }}>Source</th>
              <th style={{ minWidth: "3000px" }}>Mots-Clés</th>
              <th style={{ minWidth: "7000px" }}>Contenu</th>
            </tr>
          </thead>
          <tbody>
            {paginatedEntries.length > 0 ? (
              paginatedEntries.map((entry) => (
                <tr key={entry.source}>
                  <td>{entry.source}</td>
                  <td>{entry.keywords ? entry.keywords.join(", ") : ""}</td>
                  <td>{entry.content}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" className="text-center">
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

export default NavisanteTable;
