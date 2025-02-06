import React, { useState } from "react";
import axios from "axios";
import { Button } from "react-bootstrap";
import { Send} from "@mui/icons-material";
import "bootstrap/dist/css/bootstrap.min.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const ChatbotNavisanteInterface = () => {
  const [chat, setChat] = useState([]);
  const [query, setQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");

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
      const { answer, sources, cost } = response.data;
      setChat([...chat, { question: query, answer, sources }]);
      setQuery(""); // Clear input
      const storedAuth = localStorage.getItem("isAuthenticated");
      if (storedAuth === "true") {
        setResponseMessage(`Requête traitée avec succès! Coût total: $${cost.toFixed(4)}`);
      } else {
        setResponseMessage(`Requête traitée avec succès!`);
      }
    } catch (error) {
      console.error("Erreur lors du traitement de la requête:", error);
      setResponseMessage("Échec du traitement de votre requête:", error);
    } finally {
      setIsProcessing(false);
    }
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
      <h1 className="text-center">Chatbot Navisanté</h1>

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

      {/* Response Message */}
      {responseMessage && (
        <div className="alert alert-info text-center mt-3" role="alert">
          {responseMessage}
        </div>
      )}
    </div>
  );
};

export default ChatbotNavisanteInterface;
