
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import api from "../api/axios";
import "../styles/DetallePostulacion.css";
import ReproductorDemo from "../components/ReproductorDemo";

function formatearFecha(fecha) {
  if (!fecha) return "No disponible";

  const valor = new Date(fecha);

  if (Number.isNaN(valor.getTime())) return "No disponible";

  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "long",
    timeStyle: "short",
  }).format(valor);
}

const nombresEstadoPostulacion = {
  recibida: "Recibida",
  en_revision: "En revisión",
  seleccionada: "Seleccionada",
  descartada: "Descartada",
};

function formatearEstadoPostulacion(estado) {
  return nombresEstadoPostulacion[estado] || "Sin estado";
}

function formatearTamano(bytes) {
  if (typeof bytes !== "number") return "No disponible";

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatearDuracion(segundos) {
  if (typeof segundos !== "number") return "No disponible";

  const total = Math.floor(segundos);
  const horas = Math.floor(total / 3600);
  const minutos = Math.floor((total % 3600) / 60);
  const resto = total % 60;

  if (horas > 0) {
    return `${horas}:${String(minutos).padStart(2, "0")}:${String(resto).padStart(2, "0")}`;
  }

  return `${minutos}:${String(resto).padStart(2, "0")}`;
}

function obtenerUrlSegura(valor) {
  if (!valor) return null;

  try {
    const url = new URL(valor);

    if (!["http:", "https:"].includes(url.protocol)) {
      return null;
    }

    return url.href;
  } catch {
    return null;
  }
}

function Campo({ etiqueta, valor }) {
  return (
    <div className="detalle-campo">
      <span>{etiqueta}</span>
      <p>{valor || "No informado"}</p>
    </div>
  );
}

function formatearPuntaje(valor) {
  if (typeof valor !== "number") {
    return "No evaluable";
  }

  return `${valor.toLocaleString("es-CL", {
    maximumFractionDigits: 2,
  })}/100`;
}

function formatearEtiqueta(clave) {
  const etiquetas = {
    puntaje_audiencia: "Puntaje de audiencia",
    puntaje_fidelidad: "Puntaje de fidelidad",
    ratio_reproducciones_oyente: "Reproducciones por oyente",
    puntaje_likes: "Puntaje de likes",
    puntaje_comentarios: "Puntaje de comentarios",
    likes_promedio: "Promedio de likes",
    comentarios_promedio: "Promedio de comentarios",
    tasa_likes_pct: "Tasa de likes",
    tasa_comentarios_pct: "Tasa de comentarios",
    seguidores: "Seguidores",
    publicaciones_evaluadas: "Publicaciones evaluadas",
    caracteres_biografia: "Caracteres de biografía",
    nombre_artistico: "Nombre artístico",
    correo_contacto: "Correo de contacto",
    tipo_proyecto: "Tipo de proyecto",
    spotify_enlace: "Enlace de Spotify",
    identidad_musicbrainz: "Identidad MusicBrainz",
    instagram_enlace: "Enlace de Instagram",
    fuentes_fechas: "Vigencia de fuentes",
    demos_trazables: "Demos trazables",
  };

  return etiquetas[clave] || clave.replaceAll("_", " ");
}

function formatearValor(valor) {
  if (valor === null || valor === undefined) {
    return "No disponible";
  }

  if (typeof valor === "boolean") {
    return valor ? "Sí" : "No";
  }

  if (Array.isArray(valor)) {
    return valor.join(", ");
  }

  if (typeof valor === "number") {
    return valor.toLocaleString("es-CL", {
      maximumFractionDigits: 2,
    });
  }

  return String(valor);
}

function obtenerTextoScore(score, estadoEvaluacion) {
  if (typeof score === "number") {
    return `${score.toLocaleString("es-CL", {
      maximumFractionDigits: 2,
    })}/100`;
  }

  if (estadoEvaluacion === "no_evaluable") {
    return "No evaluable";
  }

  return "No disponible";
}

function obtenerTextoRiesgo(nivelRiesgo, estadoEvaluacion) {
  if (nivelRiesgo) {
    return nivelRiesgo;
  }

  if (estadoEvaluacion === "no_evaluable") {
    return "Sin clasificación";
  }

  return "No disponible";
}

function obtenerTextoEstado(estadoEvaluacion) {
  if (estadoEvaluacion === "evaluable") {
    return "Evaluable";
  }

  if (estadoEvaluacion === "no_evaluable") {
    return "No evaluable";
  }

  return "Sin estado";
}

function obtenerClaseEstado(estadoEvaluacion) {
  return estadoEvaluacion === "evaluable"
    ? "reporte-texto-ok"
    : "reporte-texto-error";
}

function formatearNombreDimension(dimension) {
  const etiquetas = {
    q_audio: "Q_audio",
    q_streaming: "Q_streaming",
    q_rrss: "Q_RRSS",
    q_presskit: "Q_presskit",
    q_consistencia: "Q_consistencia",
  };

  return etiquetas[dimension] || dimension;
}

function DimensionEvaluacion({
  titulo,
  descripcion,
  dimension,
  clavePuntaje,
}) {
  const puntaje =
    typeof dimension === "number"
      ? dimension
      : dimension?.[clavePuntaje];

  const desglose = dimension?.desglose || {};

  const camposExcluidos = [
    clavePuntaje,
    "estado",
    "desglose",
    "criterios_no_evaluables",
    "fuentes_desactualizadas",
    "campos_obligatorios_faltantes",
    "fuente",
    "fecha_obtencion",
    "estado_metricas",
  ];

  const detalles =
    dimension && typeof dimension === "object"
      ? Object.entries(dimension).filter(
          ([clave, valor]) =>
            !camposExcluidos.includes(clave) &&
            valor !== null &&
            valor !== undefined
        )
      : [];

  const criteriosNoEvaluables =
    dimension?.criterios_no_evaluables || [];

  const fuentesDesactualizadas =
    dimension?.fuentes_desactualizadas || [];

  const camposFaltantes =
    dimension?.campos_obligatorios_faltantes || [];

  return (
    <article className="reporte-dimension">

      <div className="reporte-dimension-header">
        <div>
          <h3>{titulo}</h3>
          <p>{descripcion}</p>
        </div>

        <strong className="reporte-dimension-puntaje">
          {formatearPuntaje(puntaje)}
        </strong>
      </div>

      {dimension?.estado && (
        <span
          className={`reporte-dimension-estado ${
            dimension.estado === "evaluable"
              ? "reporte-estado-ok"
              : "reporte-estado-error"
          }`}
        >
          {dimension.estado === "evaluable"
            ? "Evaluable"
            : "No evaluable"}
        </span>
      )}

      {Object.keys(desglose).length > 0 && (
        <div className="reporte-desglose">
          <h4>Desglose del puntaje</h4>

          {Object.entries(desglose).map(([clave, valor]) => (
            <div className="reporte-desglose-item" key={clave}>
              <span>{formatearEtiqueta(clave)}</span>
              <strong>{formatearValor(valor)}</strong>
            </div>
          ))}
        </div>
      )}

      {detalles.length > 0 && (
        <div className="reporte-desglose">
          <h4>Indicadores</h4>

          {detalles.map(([clave, valor]) => (
            <div className="reporte-desglose-item" key={clave}>
              <span>{formatearEtiqueta(clave)}</span>
              <strong>
                {formatearValor(valor)}
                {clave.endsWith("_pct") ? "%" : ""}
              </strong>
            </div>
          ))}
        </div>
      )}

      {criteriosNoEvaluables.length > 0 && (
        <div className="reporte-advertencia">
          <strong>Criterios sin evaluar</strong>

          <ul>
            {criteriosNoEvaluables.map((criterio, index) => (
              <li key={index}>{formatearEtiqueta(criterio)}</li>
            ))}
          </ul>
        </div>
      )}

      {camposFaltantes.length > 0 && (
        <div className="reporte-advertencia">
          <strong>Campos obligatorios faltantes</strong>

          <ul>
            {camposFaltantes.map((campo, index) => (
              <li key={index}>{formatearEtiqueta(campo)}</li>
            ))}
          </ul>
        </div>
      )}

      {fuentesDesactualizadas.length > 0 && (
        <div className="reporte-advertencia">
          <strong>Fuentes desactualizadas</strong>

          <ul>
            {fuentesDesactualizadas.map((fuente, index) => (
              <li key={index}>{formatearValor(fuente)}</li>
            ))}
          </ul>
        </div>
      )}

    </article>
  );
}

function DetallePostulacion() {
  const { postulacionId } = useParams();
  const navigate = useNavigate();

  const [postulacion, setPostulacion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [demoActivaId, setDemoActivaId] = useState(null);
  const [evaluacion, setEvaluacion] = useState(null);
  const [loadingEvaluacion, setLoadingEvaluacion] = useState(true);
  const [generandoEvaluacion, setGenerandoEvaluacion] = useState(false);
  const [errorEvaluacion, setErrorEvaluacion] = useState("");
  // HU013 - Gestión del estado de postulación
  const [cambiandoEstado, setCambiandoEstado] = useState(false);
  const [errorEstado, setErrorEstado] = useState("");
  const [mensajeEstado, setMensajeEstado] = useState("");

  useEffect(() => {
    let activo = true;

    const cargarPostulacion = async () => {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        navigate("/acceso", { replace: true });
        return;
      }

      try {
        const response = await api.get(
          `/postulaciones/${postulacionId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (activo) {
          setPostulacion(response.data);
        }
      } catch (err) {
        if (!activo) return;

        const status = err.response?.status;

        if (status === 401) {
          sessionStorage.removeItem("access_token");
          navigate("/acceso", { replace: true });
          return;
        }

        if (status === 403) {
          setError("No tienes permiso para consultar esta postulación.");
        } else if (status === 404) {
          setError("No se encontró la postulación solicitada.");
        } else {
          setError(
            "No fue posible cargar la información del artista. Inténtalo nuevamente."
          );
        }

        console.error("Error al consultar postulación:", err);
      } finally {
        if (activo) {
          setLoading(false);
        }
      }
    };

    cargarPostulacion();

    return () => {
      activo = false;
    }; 
  }, [postulacionId, navigate]);

  useEffect(() => {
    let activo = true;

    const cargarEvaluacion = async () => {
      const token = sessionStorage.getItem("access_token");

      if (!token) {
        navigate("/acceso", { replace: true });
        return;
      }

      setLoadingEvaluacion(true);
      setEvaluacion(null);
      setErrorEvaluacion("");

      try {
        const response = await api.get(
          `/postulaciones/${postulacionId}/viabilidad`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (activo) {
          setEvaluacion(response.data);
        }

      } catch (err) {
        if (!activo) return;

        const status = err.response?.status;

        if (status === 404) {
          // Todavía no existe una evaluación.
          setEvaluacion(null);

        } else if (status === 401) {
          sessionStorage.removeItem("access_token");
          navigate("/acceso", { replace: true });

        } else if (status === 403) {
          setErrorEvaluacion(
            "No tienes permisos para consultar esta evaluación."
          );

        } else {
          setErrorEvaluacion(
            "No fue posible recuperar el reporte de evaluación."
          );
        }

      } finally {
        if (activo) {
          setLoadingEvaluacion(false);
        }
      }
    };

    cargarEvaluacion();

    return () => {
      activo = false;
    };

  }, [postulacionId, navigate]);

  const generarEvaluacion = async () => {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/acceso", { replace: true });
      return;
    }

    if (generandoEvaluacion) {
      return;
    }

    setGenerandoEvaluacion(true);
    setErrorEvaluacion("");

    try {
      const response = await api.post(
        `/postulaciones/${postulacionId}/evaluacion`,
        null,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.data?.viabilidad) {
        throw new Error(
          "El servidor no devolvió un reporte de evaluación válido."
        );
      }

      setEvaluacion(response.data);

    } catch (err) {
      console.error(
        "Error al generar evaluación:",
        err
      );

      const status = err.response?.status;

      if (status === 401) {
        sessionStorage.removeItem("access_token");
        navigate("/acceso", { replace: true });
        return;
      }

      if (status === 403) {
        setErrorEvaluacion(
          "No tienes permisos para generar evaluaciones."
        );

      } else if (status === 404) {
        setErrorEvaluacion(
          "No se encontró la postulación solicitada."
        );

      } else {
        setErrorEvaluacion(
          err.response?.data?.detail ||
          err.message ||
          "No fue posible generar la evaluación."
        );
      }

    } finally {
      setGenerandoEvaluacion(false);
    }
  };

  // =====================================================
  // HU013 - CAMBIAR ESTADO DE POSTULACIÓN
  // =====================================================

  const cambiarEstado = async (estadoNuevo) => {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      navigate("/acceso", { replace: true });
      return;
    }

    if (cambiandoEstado) {
      return;
    }

    // Validar transiciones desde el frontend.
    // El backend mantiene la validación definitiva.
    const transicionesPermitidas = {
      recibida: ["en_revision"],
      en_revision: ["seleccionada", "descartada"],
      seleccionada: [],
      descartada: [],
    };

    const estadoActual = postulacion?.estado;

    if (
      !transicionesPermitidas[estadoActual]?.includes(estadoNuevo)
    ) {
      setErrorEstado(
        "La transición de estado solicitada no está permitida."
      );
      return;
    }

    // Solicitar confirmación para decisiones finales.
    if (estadoNuevo === "seleccionada") {
      const confirmar = window.confirm(
        "¿Confirmas que deseas seleccionar esta postulación?"
      );

      if (!confirmar) return;
    }

    if (estadoNuevo === "descartada") {
      const confirmar = window.confirm(
        "¿Confirmas que deseas descartar esta postulación? Esta decisión es definitiva."
      );

      if (!confirmar) return;
    }

    setCambiandoEstado(true);
    setErrorEstado("");
    setMensajeEstado("");

    try {
      const response = await api.patch(
        `/postulaciones/${postulacionId}/estado`,
        {
          estado: estadoNuevo,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Actualizar la información visible sin recargar la página.
      setPostulacion((actual) => ({
        ...actual,
        estado: response.data.estado_nuevo,
        updated_at:
          response.data.fecha_actualizacion || actual.updated_at,
      }));

      setMensajeEstado(
        response.data.mensaje ||
        "El estado de la postulación fue actualizado correctamente."
      );

    } catch (err) {
      console.error("Error al cambiar estado:", err);

      const status = err.response?.status;
      const detalle = err.response?.data?.detail;

      if (status === 401) {
        sessionStorage.removeItem("access_token");
        navigate("/acceso", { replace: true });
        return;
      }

      if (status === 403) {
        setErrorEstado(
          "No tienes permisos para modificar esta postulación."
        );

      } else if (status === 404) {
        setErrorEstado(
          "No se encontró la postulación solicitada."
        );

      } else if (status === 409) {
        setErrorEstado(
          typeof detalle === "string"
            ? detalle
            : "La postulación fue modificada. Actualiza la información e inténtalo nuevamente."
        );

      } else {
        setErrorEstado(
          typeof detalle === "string"
            ? detalle
            : "No fue posible actualizar el estado de la postulación."
        );
      }

    } finally {
      setCambiandoEstado(false);
    }
  };

  if (loading) {
    return (
      <section className="detalle-postulacion">
        <div className="detalle-estado">
          <p>Cargando información del artista...</p>
        </div>
      </section>
    );
  }

  if (error || !postulacion) {
    return (
      <section className="detalle-postulacion">
        <button
          type="button"
          className="detalle-volver"
          onClick={() => navigate("/dashboard/postulaciones")}
        >
          ← Volver a postulaciones
        </button>

        <div className="detalle-estado detalle-error">
          <h2>No se pudo cargar la postulación</h2>
          <p>{error || "No hay información disponible."}</p>
        </div>
      </section>
    );
  }

  const pressKit = postulacion.press_kit || {};
  const demos = postulacion.demos || [];
  const viabilidad = evaluacion?.viabilidad || {};

  const dimensiones = viabilidad.dimensiones || {};

  const aportes = viabilidad.aportes || {};

  const fuentes = evaluacion?.fuentes || {};

  const motivosNoEvaluable =
    viabilidad.motivos_no_evaluable || [];

  const dimensionesFaltantes =
    viabilidad.dimensiones_faltantes || [];

  const estadoEvaluacion =
    viabilidad.estado || evaluacion?.estado;

  const nivelRiesgo = viabilidad.nivel_riesgo;

  const score = viabilidad.score;

  const spotifyUrl = obtenerUrlSegura(pressKit.spotify_url);
  const instagramUrl = obtenerUrlSegura(pressKit.instagram_url);

  return (
    <main className="detalle-postulacion">

      <button
        type="button"
        className="detalle-volver"
        onClick={() => navigate("/dashboard/postulaciones")}
      >
        ← Volver a postulaciones
      </button>

      <header className="detalle-header">
        <div>
          <span className="detalle-eyebrow">
            REVISIÓN A&R
          </span>

          <h1>{pressKit.nombre_artistico || postulacion.nombre_artistico}</h1>

          <p>
            {pressKit.ciudad
              ? `${pressKit.ciudad}, ${pressKit.pais}`
              : pressKit.pais}
            {" · "}
            {pressKit.tipo_proyecto}
          </p>
        </div>

        <span
          className={`detalle-estado-badge detalle-estado-badge--${postulacion.estado}`}
        >
          {formatearEstadoPostulacion(postulacion.estado)}
        </span>
      </header>

      {/* =========================================
          HU013 - GESTIÓN DEL ESTADO
      ========================================= */}

      <section className="detalle-panel detalle-gestion-estado">

        <div className="detalle-panel-header">
          <div>
            <h2>Gestión de postulación</h2>

            <p>
              Administra el proceso de revisión y registra
              la decisión correspondiente.
            </p>
          </div>
        </div>

        {errorEstado && (
          <div
            className="detalle-gestion-mensaje detalle-gestion-error"
            role="alert"
          >
            {errorEstado}
          </div>
        )}

        {mensajeEstado && (
          <div
            className={`detalle-gestion-mensaje ${postulacion.estado === "descartada" ? "detalle-gestion-descartada" : "detalle-gestion-exito"}`}
            role="status"
          >
            {mensajeEstado}
          </div>
        )}

        <div className="detalle-gestion-contenido">

          {/* ESTADO RECIBIDA */}

          {postulacion.estado === "recibida" && (
            <>
              <p>
                Esta postulación fue recibida correctamente.
                Para comenzar su evaluación, inicia formalmente
                el proceso de revisión.
              </p>

              <button
                type="button"
                className="detalle-accion-boton detalle-accion-principal"
                onClick={() => cambiarEstado("en_revision")}
                disabled={cambiandoEstado}
              >
                {cambiandoEstado
                  ? "Actualizando..."
                  : "Comenzar revisión"}
              </button>
            </>
          )}

          {/* ESTADO EN REVISIÓN */}

          {postulacion.estado === "en_revision" && (
            <>
              <p>
                La postulación se encuentra en revisión.
                Una vez finalizado el análisis, registra
                la decisión del A&R.
              </p>

              <div className="detalle-gestion-acciones">

                <button
                  type="button"
                  className="detalle-accion-boton detalle-accion-seleccionar"
                  onClick={() => cambiarEstado("seleccionada")}
                  disabled={cambiandoEstado}
                >
                  {cambiandoEstado
                    ? "Actualizando..."
                    : "Seleccionar"}
                </button>

                <button
                  type="button"
                  className="detalle-accion-boton detalle-accion-descartar"
                  onClick={() => cambiarEstado("descartada")}
                  disabled={cambiandoEstado}
                >
                  {cambiandoEstado
                    ? "Actualizando..."
                    : "Descartar"}
                </button>

              </div>
            </>
          )}

          {/* DECISIONES FINALES */}

          {["seleccionada", "descartada"].includes(
            postulacion.estado
          ) && (
            <div className="detalle-gestion-final">
              <strong>
                {postulacion.estado === "seleccionada"
                  ? "Postulación seleccionada"
                  : "Postulación descartada"}
              </strong>

              <p>
                La decisión final ya fue registrada.
                El flujo de gestión de esta postulación ha finalizado.
              </p>
            </div>
          )}

          {/* ESTADO NO RECONOCIDO */}

          {!Object.prototype.hasOwnProperty.call(
            nombresEstadoPostulacion,
            postulacion.estado
          ) && (
            <div className="detalle-gestion-mensaje detalle-gestion-error">
              El estado actual de esta postulación no es reconocido.
              No es posible realizar modificaciones.
            </div>
          )}

        </div>

      </section>

      <section className="detalle-panel">

        <div className="detalle-panel-header">
          <h2>Información general</h2>
        </div>

        <div className="detalle-campos-grid">
          <Campo
            etiqueta="Nombre artístico"
            valor={pressKit.nombre_artistico}
          />

          <Campo
            etiqueta="Correo de contacto"
            valor={pressKit.correo_contacto}
          />

          <Campo
            etiqueta="País"
            valor={pressKit.pais}
          />

          <Campo
            etiqueta="Ciudad"
            valor={pressKit.ciudad}
          />

          <Campo
            etiqueta="Tipo de proyecto"
            valor={pressKit.tipo_proyecto}
          />

          <Campo
            etiqueta="Año de inicio"
            valor={pressKit.anio_inicio}
          />
        </div>

      </section>

      <section className="detalle-panel">

        <div className="detalle-panel-header">
          <h2>Géneros musicales</h2>
        </div>

        <div className="detalle-generos">
          {pressKit.generos?.length > 0 ? (
            pressKit.generos.map((genero, index) => (
              <span key={`${genero}-${index}`}>
                {genero}
              </span>
            ))
          ) : (
            <p>No se registraron géneros musicales.</p>
          )}
        </div>

      </section>

      <section className="detalle-panel">

        <div className="detalle-panel-header">
          <h2>Biografía</h2>
        </div>

        <p className="detalle-biografia">
          {pressKit.biografia || "Sin biografía registrada."}
        </p>

        <div className="detalle-integrantes">
          <h3>Integrantes</h3>

          {pressKit.integrantes?.length > 0 ? (
            <ul>
              {pressKit.integrantes.map((integrante, index) => (
                <li key={index}>{integrante}</li>
              ))}
            </ul>
          ) : (
            <p>No se registraron integrantes.</p>
          )}
        </div>

      </section>

      <section className="detalle-panel">

        <div className="detalle-panel-header">
          <h2>Presencia digital</h2>
        </div>

        <div className="detalle-redes">

          {spotifyUrl ? (
            <a href={spotifyUrl} target="_blank" rel="noopener noreferrer">
              Spotify ↗
            </a>
          ) : (
            <span>Spotify no registrado</span>
          )}

          {instagramUrl ? (
            <a href={instagramUrl} target="_blank" rel="noopener noreferrer">
              Instagram ↗
            </a>
          ) : (
            <span>Instagram no registrado</span>
          )}

        </div>

      </section>

      <section className="detalle-panel">

        <div className="detalle-panel-header">
          <div>
            <h2>Demos musicales</h2>
            <p>{demos.length} archivo(s) registrado(s)</p>
          </div>
        </div>

        {demos.length > 0 ? (
          <div className="detalle-demos">

            {demos.map((demo, index) => {
              const audio = demo.audio_tecnico || {};
              const validacion = demo.validacion_tecnica || {};

              return (
                <article
                  className="detalle-demo"
                  key={demo.archivo_id || index}
                >

                  <div className="detalle-demo-header">
                    <div>
                      <span className="detalle-demo-numero">
                        DEMO {String(index + 1).padStart(2, "0")}
                      </span>

                      <h3>{demo.nombre}</h3>

                      <p>{demo.nombre_archivo}</p>
                    </div>

                    <span className="detalle-formato">
                      {demo.formato?.toUpperCase()}
                    </span>
                  </div>

                  <ReproductorDemo
                    postulacionId={postulacionId}
                    demo={demo}
                    activo={demoActivaId === demo.archivo_id}
                    onActivar={() => setDemoActivaId(demo.archivo_id)}
                  />

                  <div className="detalle-campos-grid">
                    <Campo
                      etiqueta="Tamaño"
                      valor={formatearTamano(demo.tamano_bytes)}
                    />

                    <Campo
                      etiqueta="Duración"
                      valor={formatearDuracion(audio.duracion_segundos)}
                    />

                    <Campo
                      etiqueta="Codec"
                      valor={audio.codec}
                    />

                    <Campo
                      etiqueta="Frecuencia de muestreo"
                      valor={
                        audio.sample_rate_hz
                          ? `${(audio.sample_rate_hz / 1000).toFixed(1)} kHz`
                          : null
                      }
                    />

                    <Campo
                      etiqueta="Bitrate"
                      valor={
                        audio.bitrate_bps
                          ? `${Math.round(audio.bitrate_bps / 1000)} kbps`
                          : null
                      }
                    />

                    <Campo
                      etiqueta="Profundidad de bits"
                      valor={
                        audio.bits_per_sample
                          ? `${audio.bits_per_sample} bits`
                          : null
                      }
                    />

                    <Campo
                      etiqueta="Canales"
                      valor={audio.channels}
                    />
                  </div>

                  <div className="detalle-validacion">
                    <div>
                      <span>Validación técnica</span>

                      <strong>
                        {validacion.valido === true
                          ? "Aprobada"
                          : validacion.valido === false
                            ? "Rechazada"
                            : "Sin información"}
                      </strong>
                    </div>

                    {validacion.q_audio !== undefined && (
                      <div>
                        <span>Q_audio</span>
                        <strong>{validacion.q_audio}/100</strong>
                      </div>
                    )}
                  </div>

                  {validacion.motivos_rechazo?.length > 0 && (
                    <div className="detalle-rechazos">
                      <strong>Motivos de rechazo</strong>

                      <ul>
                        {validacion.motivos_rechazo.map((motivo, i) => (
                          <li key={i}>{motivo}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                </article>
              );
            })}

          </div>
        ) : (
          <p>No hay demos registradas.</p>
        )}

      </section>

      {pressKit.mensaje_sello && (
        <section className="detalle-panel">
          <div className="detalle-panel-header">
            <h2>Mensaje para el sello</h2>
          </div>

          <p className="detalle-biografia">
            {pressKit.mensaje_sello}
          </p>
        </section>
      )}

      <section className="detalle-panel reporte-panel">

        <div className="detalle-panel-header reporte-header">

          <div>
            <h2>Reporte de evaluación</h2>

            <p>
              Análisis de viabilidad de la postulación
            </p>
          </div>

          <button
            type="button"
            className="reporte-boton"
            onClick={generarEvaluacion}
            disabled={generandoEvaluacion}
          >
            {generandoEvaluacion
              ? "Generando evaluación..."
              : evaluacion
                ? "Generar nueva evaluación"
                : "Generar evaluación"}
          </button>

        </div>


        {generandoEvaluacion && (
          <div
            className="reporte-progreso"
            role="status"
            aria-live="polite"
          >
            <div className="reporte-progreso-contenido">

              <span
                className="reporte-progreso-spinner"
                aria-hidden="true"
              />

              <div>
                <strong>Generando evaluación del artista...</strong>

                <p>
                  Consultando fuentes disponibles y calculando indicadores.
                  {evaluacion &&
                    " El reporte anterior seguirá visible mientras termina el proceso."}
                </p>
              </div>

            </div>

            <div
              className="reporte-progreso-barra"
              role="progressbar"
              aria-label="Generación de evaluación"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuetext="En progreso"
            >
              <span />
            </div>
          </div>
        )}


        {loadingEvaluacion ? (

          <div className="detalle-estado">
            <p>Consultando último reporte de evaluación...</p>
          </div>

        ) : (

          <>

            {errorEvaluacion && (
              <div className="reporte-mensaje-error" role="alert">
                {errorEvaluacion}
              </div>
            )}


            {!evaluacion ? (

              generandoEvaluacion ? null : (

                <div className="reporte-sin-evaluacion">
                  <h3>No existe una evaluación registrada</h3>

                  <p>
                    Genera una evaluación para analizar la viabilidad
                    de esta postulación.
                  </p>
                </div>

              )

            ) : (


              <>

                <div className="reporte-resumen">

                  <div className="reporte-resumen-card">
                    <span>Score de viabilidad</span>
                    <strong className={obtenerClaseEstado(estadoEvaluacion)}>
                      {obtenerTextoScore(score, estadoEvaluacion)}
                    </strong>
                  </div>

                  <div className="reporte-resumen-card">
                    <span>Nivel de riesgo</span>
                    <strong
                      className={`reporte-riesgo ${
                        ["bajo", "medio", "alto"].includes(
                          String(nivelRiesgo).toLowerCase()
                        )
                          ? `reporte-riesgo-${String(nivelRiesgo).toLowerCase()}`
                          : "reporte-riesgo-sin-dato"
                      }`}
                    >
                      {obtenerTextoRiesgo(nivelRiesgo, estadoEvaluacion)}
                    </strong>
                  </div>

                  <div className="reporte-resumen-card">
                    <span>Estado</span>
                    <strong className={obtenerClaseEstado(estadoEvaluacion)}>
                      {obtenerTextoEstado(estadoEvaluacion)}
                    </strong>
                  </div>

                </div>

                <div className="reporte-metadatos">

                  <div className="reporte-meta-chip">
                    <span className="reporte-meta-label">ID evaluación</span>
                    <strong>{evaluacion.evaluacion_id || "No disponible"}</strong>
                  </div>

                  <div className="reporte-meta-chip">
                    <span className="reporte-meta-label">Generado</span>
                    <strong>{formatearFecha(evaluacion.fecha_generacion)}</strong>
                  </div>

                </div>

                {estadoEvaluacion === "no_evaluable" && (

                  <div className="reporte-advertencia reporte-no-evaluable">

                    <h3>Evaluación no evaluable</h3>

                    <p>
                      No se dispone de información suficiente para
                      calcular un resultado completo.
                    </p>

                    {dimensionesFaltantes.length > 0 && (
                      <>
                        <strong>Dimensiones faltantes</strong>

                        <ul>
                          {dimensionesFaltantes.map((dimension, index) => (
                            <li key={index}>
                              {formatearNombreDimension(dimension)}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}

                    {motivosNoEvaluable.length > 0 && (
                      <>
                        <strong>Motivos</strong>

                        <ul>
                          {motivosNoEvaluable.map((motivo, index) => (
                            <li key={index}>{motivo}</li>
                          ))}
                        </ul>
                      </>
                    )}

                  </div>

                )}

                <div className="reporte-dimensiones">

                  <h3>Dimensiones evaluadas</h3>

                  <DimensionEvaluacion
                    titulo="Q_audio"
                    descripcion="Calidad técnica de las demos musicales."
                    dimension={dimensiones.q_audio}
                    clavePuntaje="q_audio"
                  />

                  <DimensionEvaluacion
                    titulo="Q_streaming"
                    descripcion="Audiencia y fidelidad de la presencia musical en plataformas."
                    dimension={dimensiones.q_streaming}
                    clavePuntaje="q_streaming"
                  />

                  <DimensionEvaluacion
                    titulo="Q_RRSS"
                    descripcion="Interacción y rendimiento de las redes sociales."
                    dimension={dimensiones.q_rrss}
                    clavePuntaje="q_rrss"
                  />

                  <DimensionEvaluacion
                    titulo="Q_presskit"
                    descripcion="Completitud y calidad de la información del artista."
                    dimension={dimensiones.q_presskit}
                    clavePuntaje="q_presskit"
                  />

                  <DimensionEvaluacion
                    titulo="Q_consistencia"
                    descripcion="Consistencia de identidad, fuentes y trazabilidad."
                    dimension={dimensiones.q_consistencia}
                    clavePuntaje="q_consistencia"
                  />

                </div>

                {Object.keys(aportes).length > 0 && (

                  <div className="reporte-aportes">

                    <h3>Aportes al score general</h3>

                    <div className="reporte-aportes-grid">

                      {Object.entries(aportes).map(([clave, valor]) => (

                        <div className="reporte-aporte" key={clave}>

                          <span>{formatearEtiqueta(clave)}</span>

                          <strong>
                            {formatearValor(valor)} pts
                          </strong>

                        </div>

                      ))}

                    </div>

                  </div>

                )}

                <div className="reporte-fuentes">

                  <h3>Fuentes de información</h3>

                  <div className="reporte-fuentes-grid">

                    {Object.entries(fuentes).map(([nombre, fuente]) => (

                      <article
                        className="reporte-fuente"
                        key={nombre}
                      >

                        <h4>
                          {nombre === "lastfm"
                            ? "Last.fm"
                            : nombre.charAt(0).toUpperCase() + nombre.slice(1)}
                        </h4>

                        <span
                          className={
                            fuente.disponible
                              ? "reporte-texto-ok"
                              : "reporte-texto-error"
                          }
                        >
                          {fuente.disponible
                            ? "Disponible"
                            : "No disponible"}
                        </span>

                        {fuente.identidad_confirmada !== undefined && (
                          <p>
                            Identidad:{" "}
                            {fuente.identidad_confirmada
                              ? "Confirmada"
                              : "No confirmada"}
                          </p>
                        )}

                        <p>
                          Fecha: {formatearFecha(fuente.fecha_obtencion)}
                        </p>

                      </article>

                    ))}

                  </div>

                </div>

              </>

            )}

          </>

        )}

      </section>

      <footer className="detalle-footer">
        <span>
          Postulación recibida: {formatearFecha(postulacion.created_at)}
        </span>

        <span>
          Última actualización: {formatearFecha(postulacion.updated_at)}
        </span>
      </footer>

    </main>
  );
}

export default DetallePostulacion;
