import React, { useState, useEffect } from "react";
import axios from "axios";
import EvenementTable from "./EvenementTable";
import DuplicateWarningModal from "./DuplicateWarningModal";
import AddModal from "./AddModal";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const EvenementInterface = ({ isMenuMinimized }) => {
  const [evenements, setEvenements] = useState([]);
  const [responseMessage, setResponseMessage] = useState("");
  const [duplications, setDuplications] = useState([]);
  const [isProcessingComplete, setIsProcessingComplete] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [costTotal, setCostTotal] = useState(0);

  useEffect(() => {
    fetchEvenements();
  }, []);

  const fetchEvenements = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/evenement/get`);
      setEvenements(response.data);
    } catch (error) {
      console.error("Erreur lors du chargement des données :", error);
      setResponseMessage("Échec du chargement des événements:", error);
    }
  };

  const handleAddEventsSubmit = async (inputData) => {
    setResponseMessage("Analyse des sources pour les événements...");
    setIsProcessingComplete(false);
    const formData = new FormData();
    formData.append("text", inputData.text || "");
    formData.append("url", inputData.url || "");
    if (inputData.file) formData.append("file", inputData.file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/evenement/process`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      const cost = response.data.cost ? response.data.cost.toFixed(4) : "0.0000";
      if (response.status === 201) {
        fetchEvenements();
        setResponseMessage(`Événements ajoutés avec succès! Coût total: $${cost}`);
      } else if (response.status === 409) {
        setDuplications(response.data.duplicates);
        setResponseMessage(`Doublons détectés. Résolution requise. Coût total: $${cost}`);
      }
    } catch (error) {
      if (error.response && error.response.status === 409) {
        const cost = error.response.data.cost ? error.response.data.cost.toFixed(4) : "0.0000";
        setCostTotal(Number(cost));
        setDuplications(error.response.data.duplicates);
        setResponseMessage(`Doublons détectés. Résolution requise. Coût total: $${cost}`);
      } else {
        console.error("Erreur lors du traitement:", error);
        setResponseMessage("Échec de l'ajout des événements:", error);
      }
    } finally {
      setIsProcessingComplete(true);
      setShowAddModal(false);
    }
  };

  const handleDuplicateActions = async (action, duplication) => {
    setResponseMessage(`Coût total: $${costTotal.toFixed(4)}. Traitement des doublons...`);
    try {
      let response;
      console.error("Duplication :", duplication);
      switch (action) {
        case "replace":
          response = await axios.put(`${API_BASE_URL}/evenement/replace`, duplication.new_entry);
          setResponseMessage("Doublon remplacé avec succès.");
          break;
        case "add":
          if (!duplication.new_entry) {
            setResponseMessage("Les données nécessaires pour l'ajout sont manquantes.");
            return;
          }
          response = await axios.post(`${API_BASE_URL}/evenement/add`, duplication.new_entry);
          setResponseMessage("Doublon ajouté comme nouvelle entrée.");
          break;
        case "cancel":
          setDuplications([]);
          setResponseMessage(`Traitement des doublons annulé. Coût total: $${costTotal.toFixed(4)}`);
          fetchEvenements();
          return;
        case "next":
          setDuplications((prev) => prev.slice(1));
          if (duplications.length <= 1) {
            setIsProcessingComplete(true);
            fetchEvenements(); // Reload entries after last duplication is resolved
            setResponseMessage(`Conflit résolu avec succès. Coût total: $${costTotal.toFixed(4)}`);
          }
          return;
        default:
          throw new Error("Action non reconnue.");
      }
      

      if (response.status === 200 || response.status === 201) {
        setDuplications((prev) => prev.slice(1));
        if (duplications.length <= 1) {
          fetchEvenements() 
          setResponseMessage(`Conflit résolu avec succès. Coût total: $${costTotal.toFixed(4)}`);
        }
      }
    } catch (error) {
      console.error("Erreur lors du traitement des doublons:", error);
      setResponseMessage("Échec du traitement des doublons:", error);
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion des événements</h1>

      <section>
        <EvenementTable evenements={evenements} />
      </section>

      <div className="d-flex justify-content-center mt-4">
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)} disabled={!isProcessingComplete}>
          Ajouter des événements
        </button>
      </div>
      {showAddModal && (
        <AddModal
          show={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddEventsSubmit}
          isMenuMinimized={isMenuMinimized}
        />
      )}

      {responseMessage && (
        <div className="alert alert-info text-center mt-3">{responseMessage}</div>
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

    </div>
  );
};

export default EvenementInterface;