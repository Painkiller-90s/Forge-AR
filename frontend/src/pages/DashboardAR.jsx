import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axios";
import "../styles/DashboardAR.css";
import logo from "../assets/forge-ar.svg";


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


  return (
    <main className="dashboard-ar-page">

      <div className="dashboard-ar-shell">

        {/* =========================
            SIDEBAR
        ========================= */}

        <aside className="dashboard-sidebar">

          <div className="dashboard-sidebar-brand">
            <div className="dashboard-brand-mark">
            <img
                src={logo}
                alt="Forge"
                className="dashboard-brand-logo"
            />
            </div>

            <div>
              <span className="dashboard-brand-title">
                Forge
              </span>

              <span className="dashboard-brand-subtitle">
                A&R
              </span>
            </div>
          </div>


          <nav className="dashboard-nav">

            <button
              type="button"
              className="dashboard-nav-item active"
            >
              <span className="dashboard-nav-icon">
                ◫
              </span>

              Resumen
            </button>

            <button
              type="button"
              className="dashboard-nav-item"
            >
              <span className="dashboard-nav-icon">
                ♫
              </span>

              Postulaciones
            </button>

            <button
              type="button"
              className="dashboard-nav-item"
            >
              <span className="dashboard-nav-icon">
                ◇
              </span>

              Análisis
            </button>

            <button
              type="button"
              className="dashboard-nav-item"
            >
              <span className="dashboard-nav-icon">
                ▤
              </span>

              Reportes
            </button>

          </nav>


          <div className="dashboard-sidebar-bottom">

            <div className="dashboard-user-mini">

              <div className="dashboard-user-avatar">
                {user?.name?.charAt(0).toUpperCase()}
              </div>

              <div className="dashboard-user-mini-info">
                <strong>{user?.name}</strong>
                <span>A&R</span>
              </div>

            </div>

            <button
              type="button"
              className="dashboard-logout"
              onClick={handleLogout}
            >
              Cerrar sesión
            </button>

          </div>

        </aside>


        {/* =========================
            CONTENIDO
        ========================= */}

        <section className="dashboard-content">

          {/* HEADER */}

          <header className="dashboard-header">

            <div>
              <span className="dashboard-eyebrow">
                PANEL A&R
              </span>

              <h1>
                Resumen de actividad
              </h1>

              <p>
                Gestiona postulaciones, revisa análisis
                técnicos y prioriza oportunidades de
                fichaje.
              </p>
            </div>


            <div className="dashboard-header-user">

              <div className="dashboard-header-avatar">
                {user?.name?.charAt(0).toUpperCase()}
              </div>

              <div>
                <strong>{user?.name}</strong>
                <span>{user?.email}</span>
              </div>

            </div>

          </header>


          {/* =========================
              MÉTRICAS
          ========================= */}

          <section className="dashboard-stats">

            <article className="dashboard-stat-card">
              <div className="dashboard-stat-top">
                <span>Postulaciones totales</span>

                <span className="dashboard-stat-icon">
                  ↗
                </span>
              </div>

              <strong className="dashboard-stat-value">
                0
              </strong>

              <p>
                Candidaturas recibidas por el sello.
              </p>
            </article>


            <article className="dashboard-stat-card">
              <div className="dashboard-stat-top">
                <span>Pendientes de revisión</span>

                <span className="dashboard-stat-icon">
                  ◷
                </span>
              </div>

              <strong className="dashboard-stat-value">
                0
              </strong>

              <p>
                Propuestas que requieren atención.
              </p>
            </article>


            <article className="dashboard-stat-card">
              <div className="dashboard-stat-top">
                <span>Riesgo bajo</span>

                <span className="dashboard-stat-icon">
                  ↓
                </span>
              </div>

              <strong className="dashboard-stat-value">
                0
              </strong>

              <p>
                Artistas con score superior a 70.
              </p>
            </article>


            <article className="dashboard-stat-card">
              <div className="dashboard-stat-top">
                <span>Analizadas</span>

                <span className="dashboard-stat-icon">
                  ✓
                </span>
              </div>

              <strong className="dashboard-stat-value">
                0
              </strong>

              <p>
                Postulaciones con reporte generado.
              </p>
            </article>

          </section>


          {/* =========================
              GRID PRINCIPAL
          ========================= */}

          <section className="dashboard-main-grid">

            {/* POSTULACIONES */}

            <article className="dashboard-panel dashboard-applications-panel">

              <div className="dashboard-panel-header">
                <div>
                  <span className="dashboard-panel-label">
                    RECEPCIÓN
                  </span>

                  <h2>
                    Postulaciones recientes
                  </h2>
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

                <h3>
                  Aún no hay postulaciones
                </h3>

                <p>
                  Cuando los artistas envíen material
                  mediante el enlace de tu sello, sus
                  candidaturas aparecerán aquí.
                </p>

              </div>

            </article>


            {/* RIESGO */}

            <article className="dashboard-panel">

              <div className="dashboard-panel-header">
                <div>
                  <span className="dashboard-panel-label">
                    ANÁLISIS
                  </span>

                  <h2>
                    Distribución de riesgo
                  </h2>
                </div>
              </div>


              <div className="dashboard-risk-list">

                <div className="dashboard-risk-item">
                  <div className="dashboard-risk-info">
                    <span className="risk-dot low" />

                    <div>
                      <strong>Riesgo bajo</strong>
                      <span>Score mayor a 70</span>
                    </div>
                  </div>

                  <strong>0</strong>
                </div>


                <div className="dashboard-risk-item">
                  <div className="dashboard-risk-info">
                    <span className="risk-dot medium" />

                    <div>
                      <strong>Riesgo medio</strong>
                      <span>Score entre 41 y 70</span>
                    </div>
                  </div>

                  <strong>0</strong>
                </div>


                <div className="dashboard-risk-item">
                  <div className="dashboard-risk-info">
                    <span className="risk-dot high" />

                    <div>
                      <strong>Riesgo alto</strong>
                      <span>Score igual o inferior a 40</span>
                    </div>
                  </div>

                  <strong>0</strong>
                </div>

              </div>


              <div className="dashboard-risk-note">
                El indicador se calculará utilizando
                calidad técnica, streaming, engagement,
                Press Kit y trazabilidad.
              </div>

            </article>

          </section>


          {/* =========================
              INFORMACIÓN INFERIOR
          ========================= */}

          <section className="dashboard-bottom-grid">

            <article className="dashboard-panel">

              <div className="dashboard-panel-header">
                <div>
                  <span className="dashboard-panel-label">
                    FLUJO
                  </span>

                  <h2>
                    Estado del proceso
                  </h2>
                </div>
              </div>


              <div className="dashboard-flow">

                <div className="dashboard-flow-item">
                  <span>01</span>

                  <div>
                    <strong>Recepción</strong>
                    <p>
                      El artista envía su postulación.
                    </p>
                  </div>
                </div>


                <div className="dashboard-flow-line" />


                <div className="dashboard-flow-item">
                  <span>02</span>

                  <div>
                    <strong>Validación</strong>
                    <p>
                      Forge analiza el material recibido.
                    </p>
                  </div>
                </div>


                <div className="dashboard-flow-line" />


                <div className="dashboard-flow-item">
                  <span>03</span>

                  <div>
                    <strong>Evaluación A&R</strong>
                    <p>
                      El equipo revisa métricas y riesgo.
                    </p>
                  </div>
                </div>

              </div>

            </article>


            <article className="dashboard-panel dashboard-account-panel">

              <span className="dashboard-panel-label">
                CUENTA
              </span>

              <h2>
                Sesión activa
              </h2>


              <div className="dashboard-account-row">
                <span>Usuario</span>
                <strong>{user?.name}</strong>
              </div>

              <div className="dashboard-account-row">
                <span>Correo</span>
                <strong>{user?.email}</strong>
              </div>

              <div className="dashboard-account-row">
                <span>Rol</span>
                <strong>A&R</strong>
              </div>

              <div className="dashboard-session-status">
                <span />
                Sesión autenticada
              </div>

            </article>

          </section>

        </section>

      </div>

    </main>
  );
}


export default DashboardAR;