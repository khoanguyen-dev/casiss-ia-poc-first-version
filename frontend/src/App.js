import React, { useState } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import SideMenu from "./SideMenu";
import AnnuaireInterface from "./AnnuaireInterface";
import EvenementInterface from "./EvenementInterface";
import NavisanteInterface from "./NavisanteInterface";
import { Box } from "@mui/material";

const App = () => {
  const [isMenuMinimized, setIsMenuMinimized] = useState(false);

  const toggleMenu = () => {
    setIsMenuMinimized(!isMenuMinimized);
  };

  return (
    <Router>
      <Box sx={{ display: "flex", height: "100vh" }}>
        {/* Side Menu */}
        <SideMenu isMinimized={isMenuMinimized} toggleMenu={toggleMenu} />

        {/* Main Content */}
        <Box
          sx={{
            flexGrow: 1,
            padding: 3,
            marginLeft: isMenuMinimized ? 2 : 2, // Adjust based on menu width
            transition: "margin-left 0.3s",
          }}
        >
          <Routes>
            <Route path="/annuaire" element={<AnnuaireInterface isMenuMinimized={isMenuMinimized} />} />
            <Route path="/evenement" element={<EvenementInterface isMenuMinimized={isMenuMinimized} />} />
            <Route path="/navisante" element={<NavisanteInterface />} />
            <Route path="/" element={<h1>Bienvenue à CASSIS IA</h1>} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
};

export default App;
