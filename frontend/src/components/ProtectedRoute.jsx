
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import api from "../api/axios";

function ProtectedRoute({ children, requiredRole }) {
  const [estado, setEstado] = useState("verificando");

  useEffect(() => {
    let activo = true;

    const verificarAcceso = async () => {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        setEstado("no_autenticado");
        return;
      }

      try {
        const response = await api.get("/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!activo) return;

        const usuario = response.data;

        if (usuario.role !== requiredRole) {
          setEstado("sin_permisos");
          return;
        }

        setEstado("autorizado");
      } catch {
        if (!activo) return;

        sessionStorage.removeItem("access_token");
        setEstado("no_autenticado");
      }
    };

    verificarAcceso();

    return () => {
      activo = false;
    };
  }, [requiredRole]);

  if (estado === "verificando") {
    return <p>Verificando acceso...</p>;
  }

  if (estado !== "autorizado") {
    return <Navigate to="/acceso" replace />;
  }

  return children;
}

export default ProtectedRoute;
