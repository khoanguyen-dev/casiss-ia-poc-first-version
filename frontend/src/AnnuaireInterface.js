import React, { useState, useEffect } from "react";
import axios from "axios";
import AnnuaireTable from "./AnnuaireTable";
import AnnuaireAddModal from "./AnnuaireAddModal";
import ConflictResolutionModal from "./ConflictResolutionModal";
import DuplicateWarningModal from "./DuplicateWarningModal";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const AnnuaireInterface = ({ isMenuMinimized }) => {
  const [entries, setEntries] = useState([]);
  const [responseMessage, setResponseMessage] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [activeConflict, setActiveConflict] = useState(null);
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
      setResponseMessage("Échec du chargement des entrées:", error);
    }
  };

  const handleUpdateAnnuaire = async (entryId, entryNom, entryPrenom) => {
    setIsProcessingComplete(false);
    setResponseMessage(`Mise à jour de l'entrée ${entryId}: ${entryNom} ${entryPrenom} ...`);
    
    try {
      const response = await fetch(`${API_BASE_URL}/annuaire/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_id: entryId })
      });

      if (!response.ok) {
        throw new Error("La réponse réseau n'est pas correcte");
      }

      const result = await response.json();

      if (result.message === "Entry processed.") {
        setResponseMessage(`L'entrée ${entryId} a été mise à jour.`);
      } else if (result.sources && result.sources.length > 0) {
        setActiveConflict({
          entry_id: result.entry_id,
          nom: result.nom,
          prenom: result.prenom,
          sources: result.sources,
        });
      }
    } catch (error) {
      console.error("Error updating annuaire:", error);
      setResponseMessage(`Échec de la mise à jour de l'entrée ${entryId}.`);
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
        setResponseMessage("Échec de l’ajout de l’entrée:", error);
      }
    } finally {
      setIsProcessingComplete(true);
      setShowAddModal(false);
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
      setResponseMessage("Échec du traitement des doublons:", error);
      setIsProcessingComplete(true);
    }
  };  

  const handleAddEntries = () => {
    setShowAddModal(true);
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
        setActiveConflict(null);
        fetchEntries();
        setIsProcessingComplete(true);
      } else {
        setResponseMessage("Échec de la résolution du conflit.");
        setIsProcessingComplete(true);
      }
    } catch (error) {
      console.error("Error resolving conflict:", error);
      setResponseMessage("Échec de la résolution du conflit:", error);
      setIsProcessingComplete(true);
    }
  };
  
  const handleCancelConflict = () => {
    setActiveConflict(null);
    fetchEntries();
    setIsProcessingComplete(true);
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion de l'annuaire</h1>

      <section>
      <AnnuaireTable entries={entries} handleUpdateAnnuaire={handleUpdateAnnuaire} isProcessingComplete={isProcessingComplete} />
        <div className="d-flex justify-content-center mt-4">
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
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddEntriesSubmit}
          isMenuMinimized={isMenuMinimized}
        />
      )}

      {duplications.length > 0 && (
        <DuplicateWarningModal
          duplicate={duplications[0]}
          onReplace={(dup) => handleDuplicateActions("replace", dup)}
          onAdd={(dup) => handleDuplicateActions("add", dup)}
          onCancel={() => handleDuplicateActions("cancel")}
          onNext={() => handleDuplicateActions("next")}
          isMenuMinimized={isMenuMinimized}
        />
      )}

      {activeConflict != null && (
        <ConflictResolutionModal
          conflict={activeConflict}
          onResolve={(resolvedData) => handleResolveConflict(resolvedData)}
          onClose={() => handleCancelConflict()} // Cancel only the active conflict
          isMenuMinimized={isMenuMinimized}
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
