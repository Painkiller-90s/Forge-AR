
import { useEffect, useState } from "react";

import api from "../api/axios";
import "../styles/BandejaPostulaciones.css";

function BandejaPostulaciones() {
  const [bandeja, setBandeja] = useState({
    postulaciones: [],
    generos_disponibles: [],
    total: 0,
  });

  const [generosSeleccionados, setGenerosSeleccionados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [recargar, setRecargar] = useState(0);

  useEffect(() => {
    let activo = true;

    const cargarPostulaciones = async () => {
      setLoading(true);
      setError("");

      const token = sessionStorage.getItem("access_token");

      if (!token) {
        setError("No se encontró una sesión activa.");
        setLoading(false);
        return;
      }

      // Enviar géneros como parámetros repetidos.
      // FastAPI los recibe como una lista.
      const params = new URLSearchParams();

      generosSeleccionados.forEach((genero) => {
        params.append("generos", genero);
      });

      try {
        const response = await api.get(
          "/postulaciones/bandeja",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            params,
          }
        );

        if (activo) {
          setBandeja(response.data);
        }

      } catch (err) {
        console.error(
          "Error al cargar postulaciones:",
          err
        );

        if (activo) {
          const detalle = err.response?.data?.detail;

          setError(
            typeof detalle === "string"
              ? detalle
              : "No fue posible cargar las postulaciones."
          );
        }

      } finally {
        if (activo) {
          setLoading(false);
        }
      }
    };

    cargarPostulaciones();

    return () => {
      activo = false;
    };

  }, [generosSeleccionados, recargar]);

  const cambiarGenero = (genero) => {
    setGenerosSeleccionados((actuales) => {
      if (actuales.includes(genero)) {
        return actuales.filter(
          (item) => item !== genero
        );
      }

      return [...actuales, genero];
    });
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return "Fecha no disponible";

    return new Intl.DateTimeFormat("es-CL", {
      dateStyle: "medium",
    }).format(new Date(fecha));
  };

  return (
    <section className="bandeja-page">

      <header className="bandeja-header">
        <div>
          <span className="dashboard-eyebrow">
            RECEPCIÓN
          </span>

          <h1>Postulaciones</h1>

          <p>
            Revisa los artistas que han postulado
            a tu sello discográfico.
          </p>
        </div>

        <button
          type="button"
          className="bandeja-refresh"
          onClick={() => setRecargar((valor) => valor + 1)}
          disabled={loading}
        >
          Actualizar
        </button>
      </header>

      <section className="bandeja-filtros">

        <div className="bandeja-filtros-header">
          <div>
            <h2>Géneros musicales</h2>

            <p>
              Selecciona uno o varios géneros
              para filtrar las postulaciones.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setGenerosSeleccionados([])}
            disabled={generosSeleccionados.length === 0}
          >
            Limpiar filtros
          </button>
        </div>

        <div className="bandeja-generos">

          {bandeja.generos_disponibles.map((genero) => (
            <label
              key={genero}
              className="bandeja-genero-option"
            >
              <input
                type="checkbox"
                checked={generosSeleccionados.includes(genero)}
                onChange={() => cambiarGenero(genero)}
              />

              <span>{genero}</span>
            </label>
          ))}

          {bandeja.generos_disponibles.length === 0 && (
            <p>
              Todavía no hay géneros registrados.
            </p>
          )}

        </div>

      </section>

      <section className="bandeja-resultados">

        <div className="bandeja-resultados-header">
          <h2>Resultados</h2>

          <span>
            {bandeja.total} postulaciones
          </span>
        </div>

        {loading && (
          <div className="bandeja-mensaje">
            Cargando postulaciones...
          </div>
        )}

        {!loading && error && (
          <div className="bandeja-mensaje bandeja-error">
            {error}
          </div>
        )}

        {!loading && !error && bandeja.total === 0 && (
          <div className="bandeja-vacia">
            <h3>No hay postulaciones</h3>

            <p>
              {generosSeleccionados.length > 0
                ? "No se encontraron postulaciones para los géneros seleccionados."
                : "Las postulaciones recibidas por tu sello aparecerán aquí."
              }
            </p>
          </div>
        )}

        {!loading && !error && bandeja.postulaciones.length > 0 && (
          <div className="bandeja-lista">

            {bandeja.postulaciones.map((postulacion) => (
              <article
                key={postulacion.id}
                className="bandeja-card"
              >

                <div className="bandeja-card-header">
                  <h3>
                    {postulacion.nombre_artistico}
                  </h3>

                  <span className="bandeja-estado">
                    {postulacion.estado}
                  </span>
                </div>

                <p className="bandeja-ubicacion">
                  {[postulacion.ciudad, postulacion.pais]
                    .filter(Boolean)
                    .join(", ")}
                </p>

                <p className="bandeja-tipo">
                  {postulacion.tipo_proyecto}
                </p>

                <div className="bandeja-tags">
                  {postulacion.generos.map((genero) => (
                    <span key={genero}>
                      {genero}
                    </span>
                  ))}
                </div>

                <div className="bandeja-card-footer">
                  <span>
                    Recibida: {formatearFecha(postulacion.created_at)}
                  </span>
                </div>

              </article>
            ))}

          </div>
        )}

      </section>

    </section>
  );
}

export default BandejaPostulaciones;
