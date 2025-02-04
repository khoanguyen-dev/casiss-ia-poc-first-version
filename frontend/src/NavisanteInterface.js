import React, { useState } from "react";
import axios from "axios";
import { Modal, Button, Form } from "react-bootstrap";
import { Send } from "@mui/icons-material";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const NavisanteInterface = () => {
  const [showModal, setShowModal] = useState(false);
  const [urls, setUrls] = useState(""); // Updated to handle multiple URLs
  const [depth, setDepth] = useState(1);
  const [maxPages, setMaxPages] = useState(1);
  const [keywords, setKeywords] = useState(""); // For user-added keywords
  const [pdfFile, setPdfFile] = useState(null);
  const [chat, setChat] = useState([]);
  const [query, setQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");

  // Function to handle scraping
  const scrapeData = async () => {
    setIsProcessing(true);
    setResponseMessage("Ajout des sources en cours...");
    try {
      const formData = new FormData();
      formData.append("depth", depth);
      formData.append("maxPages", maxPages);
      formData.append("keywords", keywords);

      if (urls.trim()) {
        const urlList = urls.split(/[\n,]/).map((url) => url.trim()).filter((url) => url);
        formData.append("urls", JSON.stringify(urlList));
      }

      if (pdfFile) {
        formData.append("pdf", pdfFile);
      }

      const response = await axios.post(`${API_BASE_URL}/navisante/scrape`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResponseMessage(response.data.message || "Ajout des sources terminé avec succès !");
    } catch (error) {
      console.error("Erreur lors de l'ajout des sources:", error);
      setResponseMessage("Échec de l'ajout des sources.");
    } finally {
      setIsProcessing(false);
      setShowModal(false);
    }
  };

  // Function to handle query
  const sendQuery = async () => {
    const chatHistory = chat
      .map((c) => ({ role: "user", content: c.question }))
      .concat(chat.map((c) => ({ role: "assistant", content: c.answer })));

    setIsProcessing(true);
    setResponseMessage("Traitement de votre requête...");
    try {
      const response = await axios.post(`${API_BASE_URL}/navisante/query`, {
        query,
        history: chatHistory,
      });
      const { answer, sources } = response.data;
      setChat([...chat, { question: query, answer, sources }]);
      setQuery(""); // Clear input
      setResponseMessage("Requête traitée avec succès !");
    } catch (error) {
      console.error("Erreur lors du traitement de la requête:", error);
      setResponseMessage("Échec du traitement de votre requête:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Function to handle cancel
  const cancelProcess = () => {
    setIsProcessing(false);
    setResponseMessage("Processus annulé.");
  };

  // Handle Key Press
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey && query.trim() && !isProcessing) {
      e.preventDefault(); // Prevent newline and submit query
      sendQuery();
    }
  };

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setQuery(e.target.value);
    const textarea = e.target;
    textarea.style.height = "auto"; // Reset height
    textarea.style.height = `${textarea.scrollHeight}px`; // Adjust to scroll height
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Navisanté</h1>

      {/* Chat Section */}
      <section>
        <div className="chat-history mt-4">
          <div className="chat-box">
            {chat.map((c, index) => (
              <div key={index} className="mb-3">
                <div className="bubble user-bubble bg-primary text-white p-3 mb-2 rounded">
                  <strong>Vous :</strong> {c.question}
                </div>
                <div className="bubble assistant-bubble bg-secondary text-white p-3 rounded">
                  <strong>Assistant :</strong> {c.answer}
                  <div className="sources mt-2">
                    <strong>Sources :</strong>{" "}
                    {c.sources.map((s, idx) => (
                      <a
                        key={idx}
                        href={s}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="d-block"
                      >
                        {s}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Chat Input Section */}
        <div className="chat-input mt-4 d-flex align-items-center">
          <textarea
            value={query}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Posez une question..."
            className="form-control"
            style={{
              flex: 1,
              resize: "none",
              overflow: "hidden",
            }}
            rows={1}
            disabled={isProcessing}
          />
          <Button
            onClick={sendQuery}
            disabled={!query.trim() || isProcessing}
            className="d-flex align-items-center justify-content-center ms-2"
            style={{
              backgroundColor: "#3b82f6",
              color: "#fff",
              borderRadius: "50%",
              width: "45px",
              height: "45px",
              padding: "0",
              boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.2)",
            }}
          >
            <Send />
          </Button>
        </div>
      </section>

      {/* Buttons Section */}
      <section className="mt-4 d-flex">
        <Button
          variant="warning"
          onClick={() => setShowModal(true)}
          disabled={isProcessing}
          className="me-2"
        >
          Ajouter des sources
        </Button>
        <Button
          variant="danger"
          onClick={cancelProcess}
          disabled={!isProcessing}
        >
          Annuler
        </Button>
      </section>

      {/* Scraping Modal */}
      <Modal show={showModal} onHide={() => { setShowModal(false); setUrls(""); setPdfFile(null); }}>
        <Modal.Header closeButton>
          <Modal.Title>Ajouter des sources</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>URLs (séparées par des virgules ou des lignes)</Form.Label>
              <Form.Control as="textarea" value={urls} onChange={(e) => setUrls(e.target.value)} rows={3} />
            </Form.Group>
            <Form.Group>
              <Form.Label>Profondeur</Form.Label>
              <Form.Control type="number" value={depth} onChange={(e) => setDepth(Number(e.target.value))} />
            </Form.Group>
            <Form.Group>
              <Form.Label>Nombre maximal de pages</Form.Label>
              <Form.Control type="number" value={maxPages} onChange={(e) => setMaxPages(Number(e.target.value))} />
            </Form.Group>
            <Form.Group>
              <Form.Label>Mots-clés (séparés par des virgules)</Form.Label>
              <Form.Control type="text" value={keywords} onChange={(e) => setKeywords(e.target.value)} />
            </Form.Group>
            <Form.Group>
              <Form.Label>Télécharger un fichier PDF</Form.Label>
              <Form.Control type="file" accept="application/pdf" onChange={(e) => setPdfFile(e.target.files[0])} />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Fermer
          </Button>
          <Button variant="primary" onClick={scrapeData} disabled={isProcessing}>
            {isProcessing ? "Ajout en cours..." : "Ajouter"}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Response Message */}
      {responseMessage && (
        <div className="alert alert-info text-center mt-3" role="alert">
          {responseMessage}
        </div>
      )}
    </div>
  );
};

export default NavisanteInterface;
