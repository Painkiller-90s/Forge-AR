import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axios";
import "../styles/DashboardAR.css";
import DashboardSidebar from "../components/DashboardSidebar";

function DashboardAR() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);


  useEffect(() => {
    const loadUser = async () => {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        navigate("/acceso");
        return;
      }

      try {
        const response = await api.get("/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.data.role !== "ar") {
          navigate("/admin");
          return;
        }

        setUser(response.data);

      } catch (error) {
        console.error("Error al validar sesión:", error);

        sessionStorage.removeItem("access_token");

        navigate("/acceso");

      } finally {
        setLoadingUser(false);
      }
    };

    loadUser();

  }, [navigate]);


  const handleLogout = () => {
    sessionStorage.removeItem("access_token");

    navigate("/acceso");
  };


  if (loadingUser) {
    return (
      <main className="dashboard-ar-page">

        <div className="dashboard-ar-loading">
          <span className="dashboard-ar-loading-dot" />

          <p>Cargando panel...</p>
        </div>

      </main>
    );
  }


  const stats = [
    {
      label: "Postulaciones",
      value: 0,
    },
    {
      label: "Pendientes",
      value: 0,
    },
    {
      label: "Analizadas",
      value: 0,
    },
  ];


  return (
    <main className="dashboard-ar-page">

      <div className="dashboard-ar-shell">

        <DashboardSidebar
          user={user}
          onLogout={handleLogout}
        />


        <section className="dashboard-content">

          <header className="dashboard-header">
            <span className="dashboard-eyebrow">
              PANEL A&R
            </span>

            <h1>Resumen</h1>

            <p>
              Revisa y gestiona las postulaciones recibidas
              por tu sello.
            </p>
          </header>


          <section className="dashboard-stats">

            {stats.map((stat) => (
              <article
                key={stat.label}
                className="dashboard-stat-card"
              >
                <span>{stat.label}</span>

                <strong>
                  {stat.value}
                </strong>
              </article>
            ))}

          </section>


          <section className="dashboard-panel">

            <div className="dashboard-panel-header">

              <div>
                <span className="dashboard-panel-label">
                  RECEPCIÓN
                </span>

                <h2>Postulaciones recientes</h2>
              </div>

              <button
                type="button"
                className="dashboard-text-button"
              >
                Ver todas
              </button>

            </div>


            <div className="dashboard-empty-state">

              <div className="dashboard-empty-icon">
                ♫
              </div>

              <h3>Aún no hay postulaciones</h3>

              <p>
                Las candidaturas enviadas mediante el enlace
                de tu sello aparecerán aquí.
              </p>

            </div>

          </section>

        </section>

      </div>

    </main>
  );
}


export default DashboardAR;