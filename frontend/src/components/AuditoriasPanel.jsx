
import { useEffect, useState } from "react";
import api from "../api/axios";

const nombresAccion = {
  CONSULTA_POSTULACION: "Consulta de postulación",
  ACCESO_DEMO_AUTORIZADO: "Acceso autorizado a demo",
  CAMBIO_ESTADO_POSTULACION: "Cambio de estado de postulación",
  DECISION_FINAL_POSTULACION: "Decisión final de postulación",
};

const nombresEstado = {
  recibida: "Recibida",
  en_revision: "En revisión",
  seleccionada: "Seleccionada",
  descartada: "Descartada",
};

function formatearEstado(estado) {
  if (!estado) return "—";

  return nombresEstado[estado] ?? estado;
}

function formatearFechaUTC(fecha) {
  if (!fecha) return "—";

  const fechaDate = new Date(fecha);

  if (Number.isNaN(fechaDate.getTime())) {
    return "—";
  }

  return (
    fechaDate.toLocaleString("es-CL", {
      timeZone: "UTC",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    }) + " UTC"
  );
}

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
          setRegistros(
            Array.isArray(respuesta.data)
              ? respuesta.data
              : []
          );
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

      {cargando && (
        <p>Cargando auditorías...</p>
      )}

      {error && (
        <p role="alert">{error}</p>
      )}

      {!cargando && !error && registros.length === 0 && (
        <p>No existen auditorías registradas.</p>
      )}

      {!cargando && !error && registros.length > 0 && (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              textAlign: "left",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr>
                <th>Acción</th>
                <th>Usuario</th>
                <th>Recurso</th>
                <th>Postulación</th>
                <th>Estado anterior</th>
                <th>Estado nuevo</th>
                <th>Fecha UTC</th>
              </tr>
            </thead>

            <tbody>
              {registros.map((registro, index) => (
                <tr
                  key={
                    registro.id ??
                    registro._id ??
                    `${registro.fecha}-${registro.accion}-${index}`
                  }
                >
                  <td>
                    {nombresAccion[registro.accion] ??
                      registro.accion ??
                      "—"}
                  </td>

                  <td>
                    {registro.usuario_nombre ||
                      registro.usuario_id ||
                      "—"}
                  </td>

                  <td>
                    {registro.recurso ?? "—"}
                  </td>

                  <td>
                    {registro.postulacion_id ?? "—"}
                  </td>

                  <td>
                    {formatearEstado(
                      registro.estado_anterior
                    )}
                  </td>

                  <td>
                    {formatearEstado(
                      registro.estado_nuevo
                    )}
                  </td>

                  <td>
                    {formatearFechaUTC(registro.fecha)}
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
