import { useState } from "react";
import { useNavigate } from "react-router-dom"; // ✅ Correct import
import { Box, Button, Modal, TextField, Typography, Alert } from "@mui/material";

const LoginInterface = ({ setAuth }) => {
    const [open, setOpen] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate(); // ✅ Correct usage
  
    const handleAdminLogin = () => {
      if (username === "admin" && password === "cassis-ia") {
        setAuth(true);
        localStorage.setItem("isAuthenticated", "true");
        navigate(window.location.pathname);
      } else {
        setError("Nom d'utilisateur ou mot de passe incorrect");
      }
    };
  
    const handleKeyPress = (event) => {
      if (event.key === "Enter") {
        handleAdminLogin();
      }
    };
  
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <Typography variant="h4">Bienvenue à CASSIS IA</Typography>
        <Button variant="contained" sx={{ mt: 2 }} onClick={() => navigate("/chatbotnavisante")}>
          Utiliser Chatbot de NaviSanté
        </Button>
        <Button variant="outlined" sx={{ mt: 2 }} onClick={() => setOpen(true)}>
          Connexion Admin
        </Button>
  
        <Modal open={open} onClose={() => setOpen(false)}>
          <Box sx={{ p: 4, bgcolor: "background.paper", mx: "auto", mt: "20vh", width: 300, textAlign: "center" }}>
            <Typography variant="h6">Connexion Admin</Typography>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              fullWidth
              margin="normal"
              label="Nom d'utilisateur"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <TextField
              fullWidth
              margin="normal"
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <Button fullWidth variant="contained" sx={{ mt: 2 }} onClick={handleAdminLogin}>
              Se Connecter
            </Button>
          </Box>
        </Modal>
      </Box>
    );
};

export default LoginInterface;
