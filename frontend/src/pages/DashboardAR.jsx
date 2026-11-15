
import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import api from "../api/axios";
import "../styles/DashboardAR.css";

import DashboardSidebar from "../components/DashboardSidebar";
import BandejaPostulaciones from "./BandejaPostulaciones";
import DetallePostulacion from "./DetallePostulacion";

function DashboardAR() {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  const esDetallePostulacion =
    location.pathname.startsWith("/dashboard/postulaciones/");

  useEffect(() => {
    let activo = true;

    const loadUser = async () => {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        navigate("/acceso", { replace: true });
        return;
      }

      try {
        const response = await api.get("/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.data.role !== "ar") {
          navigate("/admin", { replace: true });
          return;
        }

        if (activo) {
          setUser(response.data);
        }

      } catch (error) {
        console.error("Error al validar sesión:", error);

        sessionStorage.removeItem("access_token");

        navigate("/acceso", { replace: true });

      } finally {
        if (activo) {
          setLoadingUser(false);
        }
      }
    };

    loadUser();

    return () => {
      activo = false;
    };

  }, [navigate]);

  const handleLogout = () => {
    sessionStorage.removeItem("access_token");
    navigate("/acceso", { replace: true });
  };

  const handleNavigate = (view) => {
    if (view === "postulaciones") {
      navigate("/dashboard/postulaciones");
    }
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

        <DashboardSidebar
          user={user}
          onLogout={handleLogout}
          activeView="postulaciones"
          onNavigate={handleNavigate}
        />

        <section className="dashboard-content">

          {esDetallePostulacion ? (
            <DetallePostulacion />
          ) : (
            <BandejaPostulaciones />
          )}

        </section>

      </div>

    </main>
  );
}

export default DashboardAR;
