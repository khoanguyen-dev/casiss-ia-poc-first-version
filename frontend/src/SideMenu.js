import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton, Box } from "@mui/material";
import { Home, People, Event, ChatBubbleOutline, ChevronLeft, ChevronRight } from "@mui/icons-material";

const SideMenu = ({ isMinimized, toggleMenu }) => {
  const location = useLocation();

  const menuItems = [
    { label: "Accueil", icon: <Home />, path: "/" },
    { label: "Annuaire", icon: <People />, path: "/annuaire" },
    { label: "Événement", icon: <Event />, path: "/evenement" },
    { label: "Navisanté", icon: <ChatBubbleOutline />, path: "/navisante" },
  ];

  return (
    <>
      {/* Drawer for Side Menu */}
      <Drawer
        variant="permanent"
        sx={{
          width: isMinimized ? 80 : 240,
          transition: "width 0.3s",
          "& .MuiDrawer-paper": {
            width: isMinimized ? 80 : 240,
            boxSizing: "border-box",
            overflowX: "hidden",
            backgroundColor: "#1e293b", // Dark sidebar background
            color: "#fff",
          },
        }}
      >
        {/* Header Section */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: 64,
            borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
            fontWeight: "bold",
            fontSize: "1.2rem",
            textAlign: "center",
          }}
        >
          CASSIS IA
        </Box>

        {/* Navigation Menu */}
        <List>
          {menuItems.map((item) => (
            <ListItem
              component={Link}
              to={item.path}
              key={item.label}
              selected={location.pathname === item.path}
              sx={{
                justifyContent: isMinimized ? "center" : "flex-start",
                "&.Mui-selected": {
                  backgroundColor: "#3b82f6", // Accent blue for selected
                  color: "#fff", // White text and icon for selected
                },
                "&:hover": {
                  backgroundColor: "#334155", // Subtle blue-gray hover effect
                },
                paddingLeft: isMinimized ? "0" : "24px",
                paddingRight: isMinimized ? "0" : "24px",
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: isMinimized ? "auto" : "40px",
                  color: location.pathname === item.path ? "#fff" : "inherit",
                  justifyContent: isMinimized ? "center" : "flex-start",
                }}
              >
                {item.icon}
              </ListItemIcon>
              {!isMinimized && (
                <ListItemText
                  primary={item.label}
                  sx={{
                    color: location.pathname === item.path ? "#fff" : "inherit",
                  }}
                />
              )}
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Floating Toggle Button */}
      <IconButton
        onClick={toggleMenu}
        sx={{
          position: "fixed",
          top: "50%",
          left: isMinimized ? 50 : 210, // Position based on menu width
          transform: "translateY(-50%)",
          backgroundColor: "#3b82f6", // Accent blue
          color: "#fff",
          "&:hover": {
            backgroundColor: "#2563eb", // Darker blue on hover
          },
          borderRadius: "50%",
          width: 50,
          height: 50,
          boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.2)",
          zIndex: 1201, // Above content but below overlays
        }}
      >
        {isMinimized ? <ChevronRight /> : <ChevronLeft />}
      </IconButton>
    </>
  );
};

export default SideMenu;
