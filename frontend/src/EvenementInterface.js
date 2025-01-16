import React, { useState, useEffect } from "react";
import axios from "axios";
import EvenementTable from "./EvenementTable";
import DuplicateWarningModal from "./DuplicateWarningModal";
import "bootstrap/dist/css/bootstrap.min.css";

const EvenementInterface = () => {
  const [evenements, setEvenements] = useState([]);
  const [responseMessage, setResponseMessage] = useState("");
  const [duplications, setDuplications] = useState([]);
  const [isProcessingComplete, setIsProcessingComplete] = useState(true);

  useEffect(() => {
    fetchEvenements();
  }, []);

  const fetchEvenements = async () => {
    setResponseMessage("Chargement des événements...");
    try {
      const response = await axios.get("http://127.0.0.1:5000/evenements");
      setEvenements(response.data);
      setResponseMessage("Événements chargés avec succès.");
    } catch (error) {
      console.error("Erreur lors du chargement des données :", error);
      setResponseMessage("Échec du chargement des événements.");
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
        "http://127.0.0.1:5000/process-evenement",
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
        console.error("Erreur lors du traitement :", error);
        setResponseMessage("Échec de l'ajout des événements.");
      }
    } finally {
      setIsProcessingComplete(true);
    }
  };

  const handleDuplicateActions = async (action, duplication) => {
    setResponseMessage("Traitement des doublons...");
    try {
      let response;
      console.error("Duplication :", duplication);
      if (action === "replace") {
        response = await axios.put("http://127.0.0.1:5000/replace-evenement", [
          {
            ...duplication.new_entry,
            existing_id: duplication.new_entry.existing_id,
          },
        ]);
      } else if (action === "add") {
        response = await axios.post(
          "http://127.0.0.1:5000/add-evenement",
          duplication.new_entry
        );
      }

      if (response.status === 200 || response.status === 201) {
        setDuplications((prev) => prev.slice(1));
        if (duplications.length <= 1) fetchEvenements();
      }
    } catch (error) {
      console.error("Erreur lors du traitement des doublons :", error);
      setResponseMessage("Échec du traitement des doublons.");
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion des Événements</h1>

      <section>
        <EvenementTable evenements={evenements} />
      </section>

      <section className="mt-4">
        <h2>Ajouter un Événement</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAddEventsSubmit({
              text: e.target.text.value,
              url: e.target.url.value,
              file: e.target.file.files[0],
            });
          }}
        >
          <div className="mb-3">
            <label className="form-label">Texte:</label>
            <textarea name="text" className="form-control" rows="3" />
          </div>
          <div className="mb-3">
            <label className="form-label">URL:</label>
            <input type="url" name="url" className="form-control" />
          </div>
          <div className="mb-3">
            <label className="form-label">Fichier:</label>
            <input type="file" name="file" accept=".txt,.csv,.xlsx" className="form-control" />
          </div>
          <button type="submit" className="btn btn-primary" disabled={!isProcessingComplete}>
            Ajouter
          </button>
        </form>
      </section>

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
        />
      )}

    </div>
  );
};

export default EvenementInterface;