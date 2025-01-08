import React, { useState, useEffect } from "react";
import axios from "axios";
import AnnuaireTable from "./AnnuaireTable";
import AnnuaireAddModal from "./AnnuaireAddModal";
import ConflictResolutionModal from "./ConflictResolutionModal";
import "bootstrap/dist/css/bootstrap.min.css";

const AnnuaireInterface = () => {
  const [entries, setEntries] = useState([]);
  const [responseMessage, setResponseMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeConflicts, setActiveConflicts] = useState([]);
  const [isProcessingComplete, setIsProcessingComplete] = useState(true); // Default to true

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get("http://127.0.0.1:5000/annuaire");
      setEntries(response.data);
      setResponseMessage("");
    } catch (error) {
      console.error("Error fetching data:", error);
      setResponseMessage("Failed to fetch entries.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateAnnuaire = async () => {
    setIsProcessingComplete(false);
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/update-annuaire", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const processChunk = (chunk) => {
        buffer += decoder.decode(chunk, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        lines.forEach((line) => {
          if (line.trim()) {
            try {
              const parsed = JSON.parse(line);
              console.log("Parsed line:", parsed);

              if (parsed.message === "All entries processed.") {
                setIsProcessingComplete(true);
                setIsLoading(false);
              } else if (parsed.sources && parsed.sources.length > 0) {
                const newConflict = {
                  entry_id: parsed.entry_id,
                  nom: parsed.nom,
                  prenom: parsed.prenom,
                  sources: parsed.sources.map((source) => ({
                    url: source.url,
                    conflicting_columns: source.conflicting_columns,
                  })),
                };

                setActiveConflicts((prevActive) => [...prevActive, newConflict]);
              }
            } catch (error) {
              console.error("Error parsing line:", line, error);
            }
          }
        });
      };

      const readNextChunk = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log("Stream reading complete.");
            return;
          }
          processChunk(value);
          readNextChunk();
        });
      };

      readNextChunk();
    } catch (error) {
      console.error("Error updating annuaire:", error);
      setResponseMessage("Failed to update annuaire.");
      setIsLoading(false);
    }
  };

  const handleResolveConflict = async (resolvedData, conflict) => {
    try {
      console.log("Resolved data being sent:", resolvedData);
      const response = await axios.post("http://127.0.0.1:5000/resolve-conflicts", resolvedData);

      if (response.status === 200) {
        setResponseMessage("Conflict resolved successfully!");
        setActiveConflicts((prevActive) => prevActive.filter((c) => c !== conflict));
      } else {
        setResponseMessage("Failed to resolve conflict. Unexpected server response.");
      }
    } catch (error) {
      console.error("Error resolving conflict:", error);
      setResponseMessage("Failed to resolve conflict.");
    }
  };

  const handleCancelConflict = (conflict) => {
    setActiveConflicts((prevActive) => prevActive.filter((c) => c !== conflict));
  };

  const handleAddEntries = () => {
    setShowAddModal(true);
  };

  const handleAddEntriesClose = () => {
    setShowAddModal(false);
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Annuaire Management</h1>

      {isLoading && (
        <div className="alert alert-info text-center" role="alert">
          Loading...
        </div>
      )}

      <section>
        <h2 className="mt-4">Annuaire</h2>
        <AnnuaireTable entries={entries} />
        <div className="d-flex justify-content-center mt-4">
          <button
            className="btn btn-warning mx-2"
            onClick={handleUpdateAnnuaire}
            disabled={isLoading || !isProcessingComplete}
          >
            {isLoading ? "Updating..." : "Update Entries"}
          </button>
          <button className="btn btn-primary mx-2" onClick={handleAddEntries}>
            Add Entries
          </button>
        </div>
      </section>

      {responseMessage && (
        <div className="mt-3 alert alert-info">
          <pre>{responseMessage}</pre>
        </div>
      )}

      {showAddModal && (
        <AnnuaireAddModal
          show={showAddModal}
          onClose={handleAddEntriesClose}
          onEntriesAdded={fetchEntries}
        />
      )}

      {activeConflicts.map((conflict, index) => (
        <ConflictResolutionModal
          key={index}
          conflict={conflict}
          onResolve={(resolvedData) => handleResolveConflict(resolvedData, conflict)}
          onClose={() => handleCancelConflict(conflict)}
        />
      ))}
    </div>
  );
};

export default AnnuaireInterface;
