import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Button, Modal, TextField, Typography, Alert } from "@mui/material";

const LoginInterface = ({ setAuthAdmin , setAuthUser}) => {
    const [showAdminModal, setShowAdminModal] = useState(false);
    const [showUserModal, setShowUserModal] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();
  
    const handleAdminLogin = () => {
      if (username === "admin" && password === "casiss-ia") {
        setAuthAdmin(true);
        localStorage.setItem("isAuthenticatedAdmin", "true");
        navigate(window.location.pathname);
      } else {
        setError("Nom d'utilisateur ou mot de passe incorrect");
      }
    };

    const handleUserLogin = () => {
      if (username === "user1" && password === "test1") {
        setAuthUser(true);
        localStorage.setItem("isAuthenticatedUser", "true");
        navigate(window.location.pathname);
      } else {
        setError("Nom d'utilisateur ou mot de passe incorrect");
      }
    };
  
    const handleKeyPressAdmin = (event) => {
      if (event.key === "Enter") {
        handleAdminLogin();
      }
    };

    const handleKeyPressUser = (event) => {
      if (event.key === "Enter") {
        handleUserLogin();
      }
    };
  
    return (
      <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <Typography variant="h4">Bienvenue à CASISS IA</Typography>
        <Button variant="contained" sx={{ mt: 2 }} onClick={() => setShowUserModal(true)}>
          Utiliser Chatbot de NaviSanté
        </Button>
        <Button variant="outlined" sx={{ mt: 2 }} onClick={() => setShowAdminModal(true)}>
          Connexion Admin
        </Button>
  
        <Modal open={showAdminModal} onClose={() => setShowAdminModal(false)}>
          <Box sx={{ p: 4, bgcolor: "background.paper", mx: "auto", mt: "20vh", width: 300, textAlign: "center" }}>
            <Typography variant="h6">Connexion Admin</Typography>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              fullWidth
              margin="normal"
              label="Nom d'utilisateur"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={handleKeyPressAdmin}
            />
            <TextField
              fullWidth
              margin="normal"
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPressAdmin}
            />
            <Button fullWidth variant="contained" sx={{ mt: 2 }} onClick={handleAdminLogin}>
              Se Connecter
            </Button>
          </Box>
        </Modal>

        <Modal open={showUserModal} onClose={() => setShowUserModal(false)}>
          <Box sx={{ p: 4, bgcolor: "background.paper", mx: "auto", mt: "20vh", width: 300, textAlign: "center" }}>
            <Typography variant="h6">Connexion Utilisateur</Typography>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              fullWidth
              margin="normal"
              label="Nom d'utilisateur"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={handleKeyPressUser}
            />
            <TextField
              fullWidth
              margin="normal"
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={handleKeyPressUser}
            />
            <Button fullWidth variant="contained" sx={{ mt: 2 }} onClick={handleUserLogin}>
              Se Connecter
            </Button>
          </Box>
        </Modal>

      </Box>
    );
};

export default LoginInterface;
