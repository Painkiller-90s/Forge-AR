
import { useNavigate } from "react-router-dom";
import AuditoriasPanel from "../components/AuditoriasPanel";
import GestionUsuariosPanel from "../components/GestionUsuariosPanel";
import "../styles/DashboardAR.css";

function DashboardAdmin() {
  const navigate = useNavigate();

  const handleLogout = () => {
    sessionStorage.removeItem("access_token");
    navigate("/acceso", { replace: true });
  };

  return (
    <main className="dashboard-ar-page">
      <section className="dashboard-content">
        <header className="dashboard-header dashboard-admin-header">
          <button
            type="button"
            className="dashboard-logout dashboard-admin-logout"
            onClick={handleLogout}
          >
            Cerrar sesión
          </button>
          <span className="dashboard-eyebrow">
            PANEL ADMINISTRADOR
          </span>

          <h1>Administración</h1>

          <p>
            Bienvenido al panel administrativo de Forge A&R.
          </p>
        </header>

        <AuditoriasPanel />

        <GestionUsuariosPanel />


      </section>
    </main>
  );
}

export default DashboardAdmin;
