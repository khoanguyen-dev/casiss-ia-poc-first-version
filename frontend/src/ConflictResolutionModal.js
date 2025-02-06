import React, { useState, useEffect } from "react";
import { Modal, Button, Table, Alert } from "react-bootstrap";

const ConflictResolutionModal = ({ conflict, onResolve, onClose, isMenuMinimized }) => {
  const [resolvedData, setResolvedData] = useState({});
  const [unresolvedFields, setUnresolvedFields] = useState(false);
  const [selectedSource, setSelectedSource] = useState({});

  useEffect(() => {
    console.log("Conflict received in modal:", conflict);

    if (conflict?.sources?.length) {
      const initialResolvedData = {};
      const initialSelectedSource = {};
      conflict.sources.forEach((source) => {
        Object.keys(source.conflicting_columns || {}).forEach((field) => {
          if (!["entry_id", "nom", "prenom", "id"].includes(field)) {
            if (initialResolvedData[field] === undefined) {
              initialResolvedData[field] =
                source.conflicting_columns[field]?.existing || null;
              initialSelectedSource[field] = -1; // Default to current value, not a specific source
            }
          }
        });
      });

      console.log("Initialized resolved data:", initialResolvedData);
      setResolvedData(initialResolvedData);
      setSelectedSource(initialSelectedSource);
    } else {
      console.warn("No sources provided to modal.");
    }
  }, [conflict]);

  const formatValue = (value) => {
    if (value === true) return "Oui";
    if (value === false) return "Non";
    if (value === null || value === undefined || value ==="") return "N/A";
    return value;
  };

  const parseValueForServer = (value) => {
    if (value === "Oui") return true;
    if (value === "Non") return false;
    if (value === "N/A") return null;
    return value;
  };

  const handleSelectResolution = (field, value, sourceIndex) => {
    setResolvedData((prevData) => ({
      ...prevData,
      [field]: value,
    }));
    setSelectedSource((prevSource) => ({
      ...prevSource,
      [field]: sourceIndex,
    }));
  };

  const handleSubmit = () => {
    const unresolved = Object.keys(resolvedData).some(
      (field) => resolvedData[field] === undefined
    );

    if (unresolved) {
      setUnresolvedFields(true);
    } else {
      setUnresolvedFields(false);

      const parsedUpdates = {};
      Object.keys(resolvedData).forEach((field) => {
        parsedUpdates[field] = parseValueForServer(resolvedData[field]);
      });

      const dataToSend = {
        entry_id: conflict.entry_id,
        nom: conflict.nom,
        prenom: conflict.prenom,
        updates: parsedUpdates,
      };

      console.log("Resolved data being sent to backend:", dataToSend);
      onResolve(dataToSend);
    }
  };

  if (!conflict || !conflict.sources?.length) {
    return (
      <Modal show onHide={onClose} 
        size="lg" 
        centered
        style={{
          marginLeft: isMenuMinimized ? "250px" : "400px", // Adjust dynamically
          transition: "margin-left 0.3s ease-in-out",
        }}
      >
        <Modal.Header closeButton>
          <Modal.Title>No Conflicts</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="info">No conflicts available to resolve.</Alert>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    );
  }

  return (
    <Modal show onHide={onClose} 
      size="lg" 
      centered
      style={{
        marginLeft: isMenuMinimized ? "50px" : "100px", // Adjust dynamically
        transition: "margin-left 0.3s ease-in-out",
      }}
    >
      <Modal.Header closeButton>
        <Modal.Title>
          Resolve Conflicts - {conflict.prenom} {conflict.nom} (ID: {conflict.entry_id})
        </Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ maxHeight: "60vh", overflowY: "auto" }}>
        {unresolvedFields && (
          <Alert variant="danger">Please resolve all fields before submitting.</Alert>
        )}
        <Table bordered hover>
          <thead>
            <tr>
              <th>Field</th>
              <th>Current Value</th>
              {conflict.sources.map((source, idx) => (
                <th key={idx}>
                  <a href={source.url || "#"} target="_blank" rel="noopener noreferrer">
                    Source {idx + 1}
                  </a>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.keys(conflict.sources[0]?.conflicting_columns || {})
              .filter((field) => !["entry_id", "nom", "prenom", "id"].includes(field))
              .map((field) => (
                <tr key={field}>
                  <td>{field}</td>
                  <td>
                    <Button
                      variant={
                        selectedSource[field] === -1 ? "primary" : "outline-primary"
                      }
                      size="sm"
                      onClick={() =>
                        handleSelectResolution(
                          field,
                          conflict.sources[0]?.conflicting_columns[field]?.existing,
                          -1
                        )
                      }
                    >
                      {formatValue(conflict.sources[0]?.conflicting_columns[field]?.existing)}
                    </Button>
                  </td>
                  {conflict.sources.map((source, idx) => (
                    <td key={idx}>
                      <Button
                        variant={
                          selectedSource[field] === idx
                            ? "primary"
                            : "outline-primary"
                        }
                        size="sm"
                        onClick={() =>
                          handleSelectResolution(
                            field,
                            source.conflicting_columns[field]?.new,
                            idx
                          )
                        }
                      >
                        {formatValue(source.conflicting_columns[field]?.new)}
                      </Button>
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </Table>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Resolve and Update
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ConflictResolutionModal;
