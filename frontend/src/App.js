import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Box } from "@mui/material";
import SideMenu from "./SideMenu";
import AnnuaireInterface from "./AnnuaireInterface";
import EvenementInterface from "./EvenementInterface";
import NavisanteInterface from "./NavisanteInterface";
import ChatbotNavisanteInterface from "./ChatbotNavisanteInterface";
import LoginInterface from "./LoginInterface";

const App = () => {
  const [authAdmin, setAuthAdmin] = useState(localStorage.getItem("isAuthenticatedAdmin") === "true");
  const [authUser, setAuthUser] = useState(localStorage.getItem("isAuthenticatedUser") === "true");
  const [isMenuMinimized, setIsMenuMinimized] = useState(true);
  const toggleMenu = () => setIsMenuMinimized(!isMenuMinimized);

  return (
    <Router>
      <Box sx={{ display: "flex", height: "100vh" }}>
        {authAdmin && <SideMenu isMinimized={isMenuMinimized} toggleMenu={toggleMenu} setAuthAdmin={setAuthAdmin} />}
        <Box sx={{ flexGrow: 1, padding: 3, transition: "margin-left 0.3s" }}>
          <Routes>
            <Route
              path="/"
              element={
                authAdmin ? (
                  <Navigate to="/annuaire" />
                ) : authUser ? (
                  <Navigate to="/chatbotnavisante" setAuthUser={setAuthUser}/>
                ) : (
                  <LoginInterface setAuthAdmin={setAuthAdmin} setAuthUser={setAuthUser} />
                )
              }
            />
            <Route path="/chatbotnavisante" element={authUser||authAdmin ? <ChatbotNavisanteInterface setAuthUser={setAuthUser}/> : <Navigate to="/" replace />} />
            <Route path="/annuaire" element={authAdmin ? <AnnuaireInterface /> : <Navigate to="/" replace />} />
            <Route path="/evenement" element={authAdmin ? <EvenementInterface /> : <Navigate to="/" replace />} />
            <Route path="/navisante" element={authAdmin ? <NavisanteInterface /> : <Navigate to="/" replace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
