
import { useEffect, useState } from "react";
import api from "../api/axios";

const nombresAccion = {
  CONSULTA_POSTULACION: "Consulta de postulación",
  ACCESO_DEMO_AUTORIZADO: "Acceso autorizado a demo",
};

function AuditoriasPanel() {
  const [registros, setRegistros] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;

    const cargarAuditorias = async () => {
      try {
        const token = sessionStorage.getItem("access_token");

        const respuesta = await api.get("/auditorias/", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (activo) {
          setRegistros(respuesta.data);
        }
      } catch {
        if (activo) {
          setError("No fue posible cargar las auditorías.");
        }
      } finally {
        if (activo) {
          setCargando(false);
        }
      }
    };

    cargarAuditorias();

    return () => {
      activo = false;
    };
  }, []);

  return (
    <section className="dashboard-panel">
      <span className="dashboard-panel-label">
        SEGURIDAD Y TRAZABILIDAD
      </span>

      <h2>Historial de auditorías</h2>

      <p>
        Acciones registradas de los usuarios internos de tu sello.
      </p>

      {cargando && <p>Cargando auditorías...</p>}

      {error && <p role="alert">{error}</p>}

      {!cargando && !error && registros.length === 0 && (
        <p>No existen auditorías registradas.</p>
      )}

      {!cargando && !error && (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", textAlign: "left" }}>
            <thead>
              <tr>
                <th>Acción</th>
                <th>Usuario</th>
                <th>Recurso</th>
                <th>Postulación</th>
                <th>Fecha UTC</th>
              </tr>
            </thead>

            <tbody>
              {registros.map((registro) => (
                <tr key={registro.id}>
                  <td>{nombresAccion[registro.accion] ?? registro.accion}</td>  
                  <td>{registro.usuario_nombre || registro.usuario_id}</td>
                  <td>{registro.recurso}</td>
                  <td>{registro.postulacion_id ?? "—"}</td>
                  <td>
                    {registro.fecha
                        ? `${registro.fecha.replace("T", " ").slice(0, 19)} UTC`
                        : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default AuditoriasPanel;
