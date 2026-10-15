
import { useNavigate } from "react-router-dom";

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

        <header className="dashboard-header">
          <span className="dashboard-eyebrow">
            PANEL ADMINISTRADOR
          </span>

          <h1>Administración</h1>

          <p>
            Bienvenido al panel administrativo de Forge A&R.
          </p>
        </header>

        <section className="dashboard-panel">
          <div className="dashboard-panel-header">
            <div>
              <span className="dashboard-panel-label">
                FORGE A&R
              </span>

              <h2>Panel administrativo</h2>
            </div>
          </div>

          <p>
            Has iniciado sesión con permisos de administrador.
          </p>

          <p>
            Las funciones de administración y auditoría
            se integrarán en sus historias de usuario
            correspondientes.
          </p>

          <div style={{ maxWidth: "220px", marginTop: "24px" }}>
            <button
              type="button"
              className="dashboard-logout"
              onClick={handleLogout}
            >
              Cerrar sesión
            </button>
          </div>
        </section>

      </section>
    </main>
  );
}

export default DashboardAdmin;
