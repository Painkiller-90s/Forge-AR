
import { useState } from "react";

import api from "../api/axios";

function ReproductorDemo({
  postulacionId,
  demo,
  activo,
  onActivar,
}) {
  const [audioSrc, setAudioSrc] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const habilitarReproduccion = async () => {
    if (cargando) return;

    const tokenSesion = sessionStorage.getItem("access_token");

    if (!tokenSesion) {
      setError("Tu sesión ha expirado. Inicia sesión nuevamente.");
      return;
    }

    onActivar();
    setCargando(true);
    setError("");
    setAudioSrc("");

    try {
      // Solicitar un token temporal para esta demo.
      const respuesta = await api.post(
        `/postulaciones/${postulacionId}/demos/${demo.archivo_id}/playback-token`,
        null,
        {
          headers: {
            Authorization: `Bearer ${tokenSesion}`,
          },
        }
      );

      const tokenReproduccion = respuesta.data?.token;

      if (!tokenReproduccion) {
        throw new Error("El servidor no entregó un token de reproducción.");
      }

      // Construir la URL respetando la base de Axios.
      const base = (api.defaults.baseURL || "/")
        .replace(/\/+$/, "");

      const baseUrl = new URL(
        `${base}/`,
        window.location.origin
      );

      const rutaAudio = [
        "postulaciones",
        encodeURIComponent(postulacionId),
        "demos",
        encodeURIComponent(demo.archivo_id),
        "stream",
      ].join("/");

      const url = new URL(rutaAudio, baseUrl);

      // Nunca utilizar aquí el token principal de sesión.
      url.searchParams.set("token", tokenReproduccion);

      setAudioSrc(url.toString());

    } catch (err) {
      const status = err.response?.status;

      if (status === 401) {
        setError("Tu sesión ha expirado. Inicia sesión nuevamente.");
      } else if (status === 403 || status === 404) {
        setError("No tienes acceso a esta demo.");
      } else {
        setError(
          "No fue posible habilitar la reproducción. Inténtalo nuevamente."
        );
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <section className="detalle-reproductor">
      <div className="detalle-reproductor-header">
        <div>
          <strong>Reproductor de audio</strong>
          <p>
            Escucha esta demo mediante streaming privado.
          </p>
        </div>

        <span className="detalle-reproductor-formato">
          {demo.formato?.toUpperCase()}
        </span>
      </div>

      <button
        type="button"
        className="detalle-reproductor-boton"
        onClick={habilitarReproduccion}
        disabled={cargando}
      >
        {cargando
          ? "Autorizando reproducción..."
          : audioSrc && !error
            ? "Renovar acceso"
            : "Habilitar reproducción"}
      </button>

      {activo && audioSrc && !error && (
        <div className="detalle-reproductor-audio">
          <audio
            key={audioSrc}
            controls
            preload="none"
            controlsList="nodownload"
            referrerPolicy="no-referrer"
            src={audioSrc}
            onError={() => {
              setError(
                "No se pudo reproducir el audio. " +
                "La autorización pudo vencer o el navegador " +
                "no admite este formato."
              );
            }}
          >
            Tu navegador no admite reproducción de audio HTML5.
          </audio>

          <p>
            Presiona reproducir en el controlador para escuchar la demo.
          </p>
        </div>
      )}

      {error && (
        <p className="detalle-reproductor-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

export default ReproductorDemo;
