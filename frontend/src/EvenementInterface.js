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

  useEffect(() => {
    fetchEvenements();
  }, []);

  const fetchEvenements = async () => {
    setResponseMessage("Chargement des événements...");
    try {
      const response = await axios.get(`${API_BASE_URL}/evenement/get`);
      setEvenements(response.data);
      setResponseMessage("Événements chargés avec succès.");
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

      if (response.status === 201) {
        fetchEvenements();
        setResponseMessage("Événements ajoutés avec succès !");
      } else if (response.status === 409) {
        setDuplications(response.data.duplicates);
        setResponseMessage("Doublons détectés. Résolution requise.");
      }
    } catch (error) {
      if (error.response && error.response.status === 409) {
        setDuplications(error.response.data.duplicates);
        setResponseMessage("Doublons détectés. Résolution requise.");
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
    setResponseMessage("Traitement des doublons...");
    try {
      let response;
      console.error("Duplication :", duplication);
      if (action === "replace") {
        response = await axios.put(`${API_BASE_URL}/evenement/replace`, duplication.new_entry);
      } else if (action === "add") {
        response = await axios.post(
          `${API_BASE_URL}/evenement/add`,
          duplication.new_entry
        );
      }

      if (response.status === 200 || response.status === 201) {
        setDuplications((prev) => prev.slice(1));
        if (duplications.length <= 1) fetchEvenements();
      }
    } catch (error) {
      console.error("Erreur lors du traitement des doublons:", error);
      setResponseMessage("Échec du traitement des doublons:", error);
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion des Événements</h1>

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
          onCancel={() => setDuplications([])}
          onNext={() => setDuplications((prev) => prev.slice(1))}
          isMenuMinimized={isMenuMinimized}
        />
      )}

    </div>
  );
};

export default EvenementInterface;