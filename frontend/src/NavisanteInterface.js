import React, { useState, useEffect } from "react";
import axios from "axios";
import { Modal, Button, Form } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import NavisanteTable from "./NavisanteTable";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const NavisanteInterface = () => {
  const [showModal, setShowModal] = useState(false);
  const [urls, setUrls] = useState(""); // Updated to handle multiple URLs
  const [depth, setDepth] = useState(1);
  const [maxPages, setMaxPages] = useState(1);
  const [keywords, setKeywords] = useState(""); // For user-added keywords
  const [pdfFile, setPdfFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");
  const [navisanteEntries, setNavisanteEntries] = useState([]);


  useEffect(() => {
    fetchNavisanteEntries();
  }, []);

  const fetchNavisanteEntries = async () => {
    setResponseMessage("Chargement des sources...");
    try {
      const response = await axios.get(`${API_BASE_URL}/navisante/get`);
      setNavisanteEntries(response.data);
      setResponseMessage("Sources chargés avec succès.");
    } catch (error) {
      console.error("Erreur lors du chargement des données :", error);
      setResponseMessage("Échec du chargement des sources:", error);
    }
  };

  // Function to handle scraping
  const scrapeData = async () => {
    setIsProcessing(true);
    setResponseMessage("Ajout des sources en cours...");
    try {
      const formData = new FormData();
      
      // Convert values to strings before appending
      formData.append("depth", String(depth));
      formData.append("maxPages", String(maxPages));
      formData.append("keywords", keywords);
  
      if (urls.trim()) {
        const urlList = urls.split(/[\n,]/).map((url) => url.trim()).filter((url) => url);
        formData.append("urls", JSON.stringify(urlList)); // Convert array to string
      }
  
      if (pdfFile) {
        formData.append("pdf", pdfFile);
      }
  
      const response = await axios.post(`${API_BASE_URL}/navisante/scrape`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
  
      setResponseMessage(response.data.message || "Ajout des sources terminé avec succès !");
      fetchNavisanteEntries();
    } catch (error) {
      console.error("Erreur lors de l'ajout des sources:", error);
      setResponseMessage("Échec de l'ajout des sources.");
    } finally {
      setIsProcessing(false);
      setShowModal(false);
    }
  };

  return (
    <div className="container mt-4">
      <h1 className="text-center">Gestion des sources de Navisanté</h1>

      <section>
        <NavisanteTable navisanteEntries={navisanteEntries} />
      </section>

      {/* Buttons Section */}
      <section className="mt-4 justify-content-center d-flex">
        <Button
          variant="primary"
          onClick={() => setShowModal(true)}
          disabled={isProcessing}
          className="me-2"
        >
          Ajouter des sources
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
              <Form.Label>Ou Télécharger un fichier PDF</Form.Label>
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
