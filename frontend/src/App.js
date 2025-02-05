import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { Box } from "@mui/material";
import SideMenu from "./SideMenu";
import AnnuaireInterface from "./AnnuaireInterface";
import EvenementInterface from "./EvenementInterface";
import NavisanteInterface from "./NavisanteInterface";
import ChatbotNavisanteInterface from "./ChatbotNavisanteInterface";
import LoginInterface from "./LoginInterface";

const App = () => {
  const [auth, setAuth] = useState(localStorage.getItem("isAuthenticated") === "true");
  const [isMenuMinimized, setIsMenuMinimized] = useState(true);
  const toggleMenu = () => setIsMenuMinimized(!isMenuMinimized);

  return (
    <Router>
      <Box sx={{ display: "flex", height: "100vh" }}>
        {auth && <SideMenu isMinimized={isMenuMinimized} toggleMenu={toggleMenu} setAuth={setAuth} />}
        <Box sx={{ flexGrow: 1, padding: 3, transition: "margin-left 0.3s" }}>
          <Routes>
            <Route path="/" element={auth ? <Navigate to="/annuaire" /> : <LoginInterface setAuth={setAuth} />} />
            <Route path="/chatbotnavisante" element={<ChatbotNavisanteInterface />} />
            <Route path="/annuaire" element={auth ? <AnnuaireInterface /> : <Navigate to="/" replace />} />
            <Route path="/evenement" element={auth ? <EvenementInterface /> : <Navigate to="/" replace />} />
            <Route path="/navisante" element={auth ? <NavisanteInterface /> : <Navigate to="/" replace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
