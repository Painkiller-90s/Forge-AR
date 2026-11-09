
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

function DetallePostulacion() {
  const { postulacionId } = useParams();
  const navigate = useNavigate();

  const [postulacion, setPostulacion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [demoActivaId, setDemoActivaId] = useState(null);

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

        <span className="detalle-estado-badge">
          {postulacion.estado}
        </span>
      </header>

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
