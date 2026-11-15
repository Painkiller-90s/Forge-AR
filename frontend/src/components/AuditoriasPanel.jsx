
import { useEffect, useState } from "react";
import api from "../api/axios";
import "../styles/AuditoriasPanel.css";

const POR_PAGINA = 20;

const NOMBRES_ACCION = {
  CONSULTA_POSTULACION: "Consulta de postulación",
  ACCESO_DEMO_AUTORIZADO: "Acceso autorizado a demo",
  GENERACION_EVALUACION: "Generación de evaluación",
  CAMBIO_ESTADO_POSTULACION: "Cambio de estado de postulación",
  DECISION_FINAL_POSTULACION: "Decisión final de postulación",
};

const ACCIONES_CONOCIDAS = new Set(
  Object.keys(NOMBRES_ACCION)
);

const CATEGORIAS_BASE = [
  {
    accion: null,
    nombre: "Todas las auditorías",
  },
  {
    accion: "CONSULTA_POSTULACION",
    nombre: "Consultas",
  },
  {
    accion: "ACCESO_DEMO_AUTORIZADO",
    nombre: "Accesos a demos",
  },
  {
    accion: "GENERACION_EVALUACION",
    nombre: "Evaluaciones generadas",
  },
  {
    accion: "CAMBIO_ESTADO_POSTULACION",
    nombre: "Cambios de estado",
  },
  {
    accion: "DECISION_FINAL_POSTULACION",
    nombre: "Decisiones finales",
  },
];

const NOMBRES_ESTADO = {
  recibida: "Recibida",
  en_revision: "En revisión",
  seleccionada: "Seleccionada",
  descartada: "Descartada",
};

function formatearAccion(accion) {
  if (!accion) return "Acción desconocida";

  if (NOMBRES_ACCION[accion]) {
    return NOMBRES_ACCION[accion];
  }

  return accion
    .toLowerCase()
    .replaceAll("_", " ");
}

function formatearEstado(estado) {
  if (!estado) return "—";

  return NOMBRES_ESTADO[estado] ?? estado;
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
  const [resumen, setResumen] = useState({});
  const [totalGeneral, setTotalGeneral] = useState(0);
  const [totalFiltrado, setTotalFiltrado] = useState(0);
  const [totalPaginas, setTotalPaginas] = useState(0);

  const [accionSeleccionada, setAccionSeleccionada] =
    useState(null);

  const [pagina, setPagina] = useState(1);

  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let activo = true;

    const cargarAuditorias = async () => {
      setCargando(true);
      setError("");

      try {
        const token = sessionStorage.getItem(
          "access_token"
        );

        if (!token) {
          throw new Error("No existe una sesión activa.");
        }

        const params = {
          pagina,
          por_pagina: POR_PAGINA,
        };

        if (accionSeleccionada) {
          params.accion = accionSeleccionada;
        }

        const respuesta = await api.get(
          "/auditorias/",
          {
            params,
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!activo) return;

        const datos = respuesta.data;

        setRegistros(
          Array.isArray(datos.items)
            ? datos.items
            : []
        );

        setResumen(datos.resumen ?? {});
        setTotalGeneral(datos.total_general ?? 0);
        setTotalFiltrado(datos.total ?? 0);
        setTotalPaginas(datos.total_paginas ?? 0);

      } catch (err) {
        if (activo) {
          setError(
            err.response?.data?.detail ||
            err.message ||
            "No fue posible cargar las auditorías."
          );
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
  }, [pagina, accionSeleccionada]);

  // Incorporar automáticamente acciones nuevas.
  const categoriasDinamicas = Object.keys(resumen)
    .filter(
      (accion) => !ACCIONES_CONOCIDAS.has(accion)
    )
    .map((accion) => ({
      accion,
      nombre: formatearAccion(accion),
    }));

  const categorias = [
    ...CATEGORIAS_BASE,
    ...categoriasDinamicas,
  ];

  const seleccionarCategoria = (accion) => {
    setPagina(1);
    setAccionSeleccionada(accion);
  };

  const primerRegistro =
    totalFiltrado > 0
      ? (pagina - 1) * POR_PAGINA + 1
      : 0;

  const ultimoRegistro = Math.min(
    pagina * POR_PAGINA,
    totalFiltrado
  );

  return (
    <section className="dashboard-panel audit-dashboard">
      <header className="audit-header">
        <div>
          <span className="dashboard-panel-label">
            SEGURIDAD Y TRAZABILIDAD
          </span>

          <h2>Historial de auditorías</h2>

          <p>
            Consulta y supervisa las acciones realizadas
            por los usuarios internos de tu sello.
          </p>
        </div>

        <div className="audit-total">
          <span>Total de registros</span>
          <strong>{totalGeneral}</strong>
        </div>
      </header>

      {/* Categorías de auditoría */}
      <div className="audit-category-grid">
        {categorias.map((categoria) => {
          const seleccionada =
            accionSeleccionada === categoria.accion;

          const cantidad = categoria.accion
            ? resumen[categoria.accion] ?? 0
            : totalGeneral;

          return (
            <button
              key={categoria.accion ?? "todas"}
              type="button"
              className={`audit-category-card ${
                seleccionada ? "active" : ""
              }`}
              onClick={() =>
                seleccionarCategoria(categoria.accion)
              }
              aria-pressed={seleccionada}
            >
              <span>{categoria.nombre}</span>

              <strong>{cantidad}</strong>

              <small>
                {cantidad === 1
                  ? "Registro"
                  : "Registros"}
              </small>
            </button>
          );
        })}
      </div>

      {/* Tabla de auditorías */}
      <div className="audit-records">
        <div className="audit-records-header">
          <div>
            <h3>
              {accionSeleccionada
                ? formatearAccion(accionSeleccionada)
                : "Todas las auditorías"}
            </h3>

            <p>
              {totalFiltrado} registros encontrados.
            </p>
          </div>
        </div>

        {cargando && (
          <p>Cargando auditorías...</p>
        )}

        {error && (
          <p className="audit-error" role="alert">
            {error}
          </p>
        )}

        {!cargando &&
          !error &&
          registros.length === 0 && (
            <p className="audit-empty">
              No existen registros en esta categoría.
            </p>
          )}

        {!cargando &&
          !error &&
          registros.length > 0 && (
            <div className="audit-table-wrapper">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Acción</th>
                    <th>Usuario</th>
                    <th>Recurso</th>
                    <th>Postulación</th>
                    <th>Estado anterior</th>
                    <th>Estado nuevo</th>
                    <th>Método</th>
                    <th>Fecha UTC</th>
                  </tr>
                </thead>

                <tbody>
                  {registros.map((registro, index) => (
                    <tr
                      key={
                        registro.id ??
                        `${registro.fecha}-${registro.accion}-${index}`
                      }
                    >
                      <td>
                        {formatearAccion(registro.accion)}
                      </td>

                      <td>
                        {registro.usuario_nombre ||
                          registro.usuario_id ||
                          "—"}
                      </td>

                      <td>
                        {registro.recurso ?? "—"}
                      </td>

                      <td className="audit-id">
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
                        {registro.metodo ?? "—"}
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

        {/* Paginación */}
        {!cargando && !error && totalFiltrado > 0 && (
          <footer className="audit-pagination">
            <span>
              Mostrando {primerRegistro}–{ultimoRegistro}
              {" "}de {totalFiltrado} registros
            </span>

            <div className="audit-pagination-controls">
              <button
                type="button"
                disabled={pagina <= 1}
                onClick={() =>
                  setPagina((actual) => actual - 1)
                }
              >
                Anterior
              </button>

              <span>
                Página {pagina} de {totalPaginas}
              </span>

              <button
                type="button"
                disabled={
                  pagina >= totalPaginas
                }
                onClick={() =>
                  setPagina((actual) => actual + 1)
                }
              >
                Siguiente
              </button>
            </div>
          </footer>
        )}
      </div>
    </section>
  );
}

export default AuditoriasPanel;
