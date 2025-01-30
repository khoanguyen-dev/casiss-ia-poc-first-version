import React, { useState, useEffect } from "react";
import axios from "axios";
import AnnuaireTable from "./AnnuaireTable";
import AnnuaireAddModal from "./AnnuaireAddModal";
import ConflictResolutionModal from "./ConflictResolutionModal";
import DuplicateWarningModal from "./DuplicateWarningModal";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const AnnuaireInterface = () => {
  const [entries, setEntries] = useState([]);
  const [responseMessage, setResponseMessage] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeConflicts, setActiveConflicts] = useState([]);
  const [duplications, setDuplications] = useState([]);
  const [isProcessingComplete, setIsProcessingComplete] = useState(true);

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    setResponseMessage("Chargement des entrées...");
    try {
      const response = await axios.get(`${API_BASE_URL}/annuaire/get`);
      setEntries(response.data);
      setResponseMessage("Entrées chargées avec succès.");
    } catch (error) {
      console.error("Error fetching data:", error);
      setResponseMessage("Échec du chargement des entrées.");
    }
  };

  const handleUpdateAnnuaire = async () => {
    setIsProcessingComplete(false);
    setResponseMessage("Mise à jour des entrées...");
    try {
      const response = await fetch(`${API_BASE_URL}/annuaire/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
  
      if (!response.ok) {
        throw new Error("La réponse réseau n'est pas correcte");
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
  
              if (parsed.message === "All entries processed.") {
                setResponseMessage("Toutes les entrées ont été traitées.");
                setIsProcessingComplete(true);
              } else if (parsed.sources && parsed.sources.length > 0) {
                const newConflict = {
                  entry_id: parsed.entry_id,
                  nom: parsed.nom,
                  prenom: parsed.prenom,
                  sources: parsed.sources,
                };
  
                // Ensure the conflict is added to the back of the queue if not already present
                setActiveConflicts((prevActive) => {
                  const conflictExists = prevActive.some(
                    (conflict) => conflict.entry_id === newConflict.entry_id
                  );
  
                  // Add the new conflict only if it doesn't already exist
                  return conflictExists ? prevActive : [...prevActive, newConflict];
                });
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
      setResponseMessage("Échec de la mise à jour des entrées.");
      setIsProcessingComplete(true);
    }
  };  

  const handleAddEntriesSubmit = async (inputData) => {
    setResponseMessage("Analyse des sources pour l’entrée...");
    setIsProcessingComplete(false);
    const formData = new FormData();
    formData.append("text", inputData.text || "");
    formData.append("url", inputData.url || "");
    if (inputData.file) formData.append("file", inputData.file);

    console.log("Sending FormData:");
    for (let pair of formData.entries()) {
        console.log(`${pair[0]}:`, pair[1]);
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/annuaire/process`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      if (response.status === 201) {
        fetchEntries();
        setResponseMessage("Nouvelle entrée ajoutée avec succès.");
        setIsProcessingComplete(true);
      } else if (response.status === 409) {
        setDuplications(response.data.duplicates);
        setResponseMessage("Doublons détectés. Résolution requise.");
      }
    } catch (error) {
      if (error.response && error.response.status === 409) {
        setDuplications(error.response.data.duplicates);
        setResponseMessage("Doublons détectés. Résolution requise.");
      } else {
        console.error("Error processing entry:", error);
        setResponseMessage("Échec de l’ajout de l’entrée.");
      }
    }
  };

  const handleDuplicateActions = async (action, duplication) => {
    setResponseMessage("Traitement des doublons...");
    try {
      let response;
  
      switch (action) {
        case "replace":
          console.log("Replace entry:", duplication); // Debugging log
          response = await axios.put(`${API_BASE_URL}/annuaire/replace`, duplication.new_entry);
          setResponseMessage("Doublon remplacé avec succès.");
          break;
  
        case "add":
          console.log("Adding new entry:", duplication.new_entry); // Debugging log
          if (!duplication.new_entry) {
            setResponseMessage("Les données nécessaires pour l'ajout sont manquantes.");
            return;
          }
          response = await axios.post(`${API_BASE_URL}/annuaire/add`, duplication.new_entry);
          setResponseMessage("Doublon ajouté comme nouvelle entrée.");
          break;
  
        case "cancel":
          setDuplications([]);
          setResponseMessage("Traitement des doublons annulé.");
          setIsProcessingComplete(true);
          fetchEntries();
          return;
  
        case "next":
          setDuplications((prev) => prev.slice(1));
          if (duplications.length <= 1) {
            setIsProcessingComplete(true);
            fetchEntries(); // Reload entries after last duplication is resolved
          }
          return;
  
        default:
          throw new Error("Action non reconnue.");
      }
  
      if (response.status === 200 || response.status === 201) {
        setDuplications((prev) => prev.slice(1));
        if (duplications.length <= 1) {
          setIsProcessingComplete(true);
          fetchEntries(); // Reload entries after last duplication is resolved
        }
      }
    } catch (error) {
      console.error("Error handling duplication:", error);
      setResponseMessage("Échec du traitement des doublons.");
      setIsProcessingComplete(true);
    }
  };  

  const handleAddEntries = () => {
    setShowAddModal(true);
  };

  const handleAddEntriesClose = () => {
    setShowAddModal(false);
    setResponseMessage("Analyse des sources pour l’entrée.");
  };

  const handleResolveConflict = async (resolvedData) => {
    setResponseMessage("Résolution du conflit...");
    try {
      const response = await axios.post(
        `${API_BASE_URL}/annuaire/resolve-conflicts`,
        resolvedData
      );
  
      if (response.status === 200) {
        setResponseMessage("Conflit résolu avec succès.");
        setActiveConflicts((prevActive) => prevActive.slice(1)); // Remove the resolved conflict
        if (activeConflicts.length === 1) {
          // All conflicts resolved, fetch updated entries
          fetchEntries();
          setIsProcessingComplete(true);
        }
      } else {
        setResponseMessage("Échec de la résolution du conflit.");
      }
    } catch (error) {
      console.error("Error resolving conflict:", error);
      setResponseMessage("Échec de la résolution du conflit.");
    }
  };
  
  const handleCancelConflict = () => {
    setActiveConflicts((prevActive) => prevActive.slice(1)); // Remove only the first conflict
    if (activeConflicts.length === 1) {
      // If no conflicts remain after this, refresh entries
      fetchEntries();
      setIsProcessingComplete(true);
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion de l'annuaire</h1>

      <section>
        <AnnuaireTable entries={entries} />
        <div className="d-flex justify-content-center mt-4">
          <button
            className="btn btn-warning mx-2"
            onClick={handleUpdateAnnuaire}
            disabled={!isProcessingComplete}
          >
            Mettre à jour les entrées
          </button>
          <button className="btn btn-primary mx-2" 
            onClick={handleAddEntries}
            disabled={!isProcessingComplete}
          >
            Ajouter des entrées
          </button>
        </div>
      </section>

      {showAddModal && (
        <AnnuaireAddModal
          show={showAddModal}
          onClose={handleAddEntriesClose}
          onSubmit={handleAddEntriesSubmit} // Pass inputs to the interface
        />
      )}

      {duplications.length > 0 && (
        <DuplicateWarningModal
          duplicate={duplications[0]}
          onReplace={(dup) => handleDuplicateActions("replace", dup)}
          onAdd={(dup) => handleDuplicateActions("add", dup)}
          onCancel={() => handleDuplicateActions("cancel")}
          onNext={() => handleDuplicateActions("next")}
        />
      )}

      {activeConflicts.length > 0 && (
        <ConflictResolutionModal
          conflict={activeConflicts[0]}
          onResolve={(resolvedData) => handleResolveConflict(resolvedData)}
          onClose={() => handleCancelConflict()} // Cancel only the active conflict
        />
      )}

      {responseMessage && (
        <div className="alert alert-info text-center mt-3" role="alert">
          {responseMessage}
        </div>
      )}

    </div>
  );
};

export default AnnuaireInterface;
