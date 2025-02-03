import React, { useState } from "react";
import { Modal, Button, Form, Alert } from "react-bootstrap";

const AnnuaireAddModal = ({ show, onClose, onSubmit, isMenuMinimized }) => {
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [fileInput, setFileInput] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const resetInputs = () => {
    setTextInput("");
    setUrlInput("");
    setFileInput(null);
    setErrorMessage("");
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();

    if (!textInput && !urlInput && !fileInput) {
      setErrorMessage("Veuillez remplir au moins un champ.");
      return;
    }

    const inputData = { text: textInput, url: urlInput, file: fileInput };
    onSubmit(inputData); // Pass the collected data to the parent
    resetInputs();
    onClose(); // Close the modal
  };

  return (
    <Modal
      show={show}
      onHide={onClose}
      centered
      style={{
        marginLeft: isMenuMinimized ? "20px" : "150px", // Adjust position dynamically
        transition: "margin-left 0.3s ease-in-out",
      }}
    >
      <Modal.Header closeButton>
        <Modal.Title>Ajouter des entrées</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <Form onSubmit={handleFormSubmit}>
          <Form.Group className="mb-3" controlId="formTextInput">
            <Form.Label>Saisir le texte :</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Entrez les données textuelles..."
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="formUrlInput">
            <Form.Label>Ou entrez une URL :</Form.Label>
            <Form.Control
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://exemple.com"
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="formFileInput">
            <Form.Label>Ou téléchargez un fichier (CSV/XLSX/TXT) :</Form.Label>
            <Form.Control
              type="file"
              accept=".txt,.csv,.xlsx"
              onChange={(e) => setFileInput(e.target.files[0])}
            />
          </Form.Group>
          <Button variant="primary" type="submit" className="w-100">
            Soumettre
          </Button>
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default AnnuaireAddModal;
