import React from "react";
import { Link, useLocation } from "react-router-dom";

const SideMenu = ({ isMinimized, toggleMenu }) => {
  const location = useLocation();

  return (
    <div
      className="d-flex flex-column bg-light position-relative"
      style={{
        height: "100vh",
        width: isMinimized ? "80px" : "400px",
        borderRight: "1px solid #ccc",
        transition: "width 0.3s",
      }}
    >
      {/* Minimize Button */}
      <button
        className="btn btn-secondary position-absolute"
        style={{
          top: "50%",
          right: "-15px",
          width: "30px",
          height: "30px",
          padding: "0",
          zIndex: 1000,
          borderRadius: "50%",
          transform: "translateY(-50%)",
        }}
        onClick={toggleMenu}
      >
        {isMinimized ? ">" : "<"}
      </button>

      {!isMinimized && <h2 className="text-center">CASSIS IA</h2>}

      <ul className="nav nav-pills flex-column">
        <li className="nav-item">
          <Link
            to="/annuaire"
            className={`nav-link ${location.pathname === "/annuaire" ? "active" : ""}`}
          >
            {isMinimized ? "A" : "Annuaire"}
          </Link>
        </li>
        <li className="nav-item">
          <Link
            to="/evenement"
            className={`nav-link ${location.pathname === "/evenement" ? "active" : ""}`}
          >
            {isMinimized ? "E" : "Événement"}
          </Link>
        </li>
        <li className="nav-item">
          <Link
            to="/navisante"
            className={`nav-link ${location.pathname === "/navisante" ? "active" : ""}`}
          >
            {isMinimized ? "N" : "Navisanté"}
          </Link>
        </li>
      </ul>
    </div>
  );
};

export default SideMenu;
