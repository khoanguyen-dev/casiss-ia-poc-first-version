import React, { memo } from "react";

const AnnuaireTable = memo(({ entries }) => (
  <section className="mt-4">
    <table className="table table-striped table-bordered">
      <thead className="table-dark">
        <tr>
          <th>ID</th>
          <th>No EAN</th>
          <th>Type</th>
          <th>Type de Fournisseur</th>
          <th>Nom</th>
          <th>Prénom</th>
          <th>Acronyme</th>
          <th>Téléphone</th>
          <th>Portable</th>
          <th>Courriel</th>
          <th>Site Web</th>
          <th>Lien Org</th>
          <th>Organisation</th>
          <th>Rôle/Activité/Spécialité</th>
          <th>Médecin</th>
          <th>Médecin Intra-Hospitalier</th>
          <th>Lu</th>
          <th>Ma</th>
          <th>Me</th>
          <th>Je</th>
          <th>Ve</th>
          <th>Sa</th>
          <th>Di</th>
          <th>Tags</th>
          <th>Sélection</th>
          <th>Commentaire</th>
          <th>Voie</th>
          <th>Numéro</th>
          <th>Complément</th>
          <th>NPA</th>
          <th>Localité</th>
          <th>Pays</th>
          <th>Coord Geo Nord</th>
          <th>Coord Geo Est</th>
          <th>Longitude</th>
          <th>Latitude</th>
          <th>Date Dernière Modification</th>
        </tr>
      </thead>
      <tbody>
        {entries.length > 0 ? (
          entries.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.id}</td>
              <td>{entry.no_ean}</td>
              <td>{entry.type}</td>
              <td>{entry.type_de_fournisseur}</td>
              <td>{entry.nom}</td>
              <td>{entry.prenom}</td>
              <td>{entry.acronyme}</td>
              <td>{entry.telephone}</td>
              <td>{entry.portable}</td>
              <td>{entry.courriel}</td>
              <td>{entry.site_web}</td>
              <td>{entry.lien_org}</td>
              <td>{entry.organisation}</td>
              <td>{entry.role_activite_specialite}</td>
              <td>{entry.medecin ? "Oui" : "Non"}</td>
              <td>{entry.medecin_intra_hospitalier ? "Oui" : "Non"}</td>
              <td>{entry.lu ? "Oui" : "Non"}</td>
              <td>{entry.ma ? "Oui" : "Non"}</td>
              <td>{entry.me ? "Oui" : "Non"}</td>
              <td>{entry.je ? "Oui" : "Non"}</td>
              <td>{entry.ve ? "Oui" : "Non"}</td>
              <td>{entry.sa ? "Oui" : "Non"}</td>
              <td>{entry.di ? "Oui" : "Non"}</td>
              <td>{entry.tags}</td>
              <td>{entry.selection}</td>
              <td>{entry.commentaire}</td>
              <td>{entry.voie}</td>
              <td>{entry.numero}</td>
              <td>{entry.complement}</td>
              <td>{entry.npa}</td>
              <td>{entry.localite}</td>
              <td>{entry.pays}</td>
              <td>{entry.coord_geo_nord}</td>
              <td>{entry.coord_geo_est}</td>
              <td>{entry.longitude}</td>
              <td>{entry.latitude}</td>
              <td>{entry.date_derniere_modification}</td> 
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="38" className="text-center">
              No entries found.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  </section>
));

export default AnnuaireTable;
