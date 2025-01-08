import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import 'bootstrap/dist/css/bootstrap.min.css'; // Import Bootstrap CSS

// Get the root element from the DOM
const rootElement = document.getElementById('root');

// Ensure the root element exists
if (rootElement) {
  // Create a root
  const root = createRoot(rootElement);

  // Render the App component
  root.render(
      <App />
  );
} else {
  console.error("Root element not found. Ensure there is a DOM element with id 'root'.");
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
