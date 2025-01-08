import React, { useState } from "react";
import { Modal, Button, Form, Alert } from "react-bootstrap";

const AnnuaireAddModal = ({ show, onClose, onEntriesAdded }) => {
  const [textInput, setTextInput] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [fileInput, setFileInput] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const resetInputs = () => {
    setTextInput("");
    setUrlInput("");
    setFileInput(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("text", textInput);
    formData.append("url", urlInput);
    if (fileInput) formData.append("file", fileInput);

    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const response = await fetch("http://127.0.0.1:5000/process-annuaire", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        onEntriesAdded(); // Refresh entries on success
        resetInputs();
        onClose(); // Close modal
      } else {
        const errorData = await response.json();
        if (response.status === 409 && errorData.duplicates) {
          setErrorMessage(
            `Duplicates found. Please resolve them in the interface.`
          );
        } else {
          setErrorMessage(errorData.error || "Failed to process the input.");
        }
      }
    } catch (error) {
      setErrorMessage("An error occurred while processing the input.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal show={show} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Add New Entries</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="formTextInput">
            <Form.Label>Enter Text:</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Enter text data..."
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="formUrlInput">
            <Form.Label>Or Enter URL:</Form.Label>
            <Form.Control
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com"
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="formFileInput">
            <Form.Label>Or Upload File (CSV/XLSX/TXT):</Form.Label>
            <Form.Control
              type="file"
              accept=".txt,.csv,.xlsx"
              onChange={(e) => setFileInput(e.target.files[0])}
            />
          </Form.Group>
          <Button
            variant="primary"
            type="submit"
            disabled={isSubmitting}
            className="w-100"
          >
            {isSubmitting ? "Submitting..." : "Submit"}
          </Button>
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default AnnuaireAddModal;
