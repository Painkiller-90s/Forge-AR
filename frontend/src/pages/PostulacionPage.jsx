import { useState } from "react";
import { useParams } from "react-router-dom";
import { useForm } from "react-hook-form";

import api from "../api/axios";
import "../styles/PostulacionPage.css";


function PostulacionPage() {
  const { selloId } = useParams();

  const [enviada, setEnviada] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm();


  const onSubmit = async (data) => {
    setErrorServidor("");

    const payload = {
      nombre_artistico: data.nombre_artistico,
      correo_contacto: data.correo_contacto,
      pais: data.pais,
      tipo_proyecto: data.tipo_proyecto,

      generos: data.generos
        .split(",")
        .map((genero) => genero.trim())
        .filter(Boolean),

      biografia: data.biografia,
      nombre_demo: data.nombre_demo,

      integrantes: data.integrantes
        ? data.integrantes
            .split(",")
            .map((integrante) => integrante.trim())
            .filter(Boolean)
        : [],

      ciudad: data.ciudad || null,

      anio_inicio: data.anio_inicio
        ? Number(data.anio_inicio)
        : null,

      spotify_url: data.spotify_url || null,
      instagram_url: data.instagram_url || null,
      mensaje_sello: data.mensaje_sello || null,

      consentimiento_datos: data.consentimiento_datos,
      autorizacion_demo: data.autorizacion_demo,
    };

    try {
      await api.post(
        `/postulaciones/${selloId}`,
        payload
      );

      setEnviada(true);
    } catch (error) {
      console.error(error);

      setErrorServidor(
        "No se pudo enviar la postulación. Intenta nuevamente."
      );
    }
  };


  if (enviada) {
    return (
      <main className="postulacion-page postulacion-success-page">

        <div className="postulacion-success">

          <span>
            POSTULACIÓN RECIBIDA
          </span>

          <h1>
            Tu proyecto fue enviado
          </h1>

          <p>
            La información de tu proyecto fue registrada
            correctamente y ya está disponible para evaluación.
          </p>

        </div>

      </main>
    );
  }


  return (
    <main className="postulacion-page">

      <h1>
        Postula tu proyecto
      </h1>

      <p>
        Completa tu información artística para enviar tu proyecto
        al sello.
      </p>


      <form
        className="postulacion-form"
        onSubmit={handleSubmit(onSubmit)}
        autoComplete="off"
        noValidate
      >

        <section>

          <h2>
            Información artística
          </h2>


          <label>
            Nombre artístico
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("nombre_artistico", {
              required: "El nombre artístico es obligatorio",

              minLength: {
                value: 2,
                message: "Debe contener al menos 2 caracteres",
              },
            })}
          />

          {errors.nombre_artistico && (
            <p>
              {errors.nombre_artistico.message}
            </p>
          )}


          <label>
            Tipo de proyecto
          </label>

          <select
            {...register("tipo_proyecto", {
              required: "Selecciona el tipo de proyecto",
            })}
          >
            <option value="">
              Selecciona una opción
            </option>

            <option value="Solista">
              Solista
            </option>

            <option value="Banda">
              Banda
            </option>

            <option value="Duo">
              Dúo
            </option>

            <option value="Proyecto">
              Proyecto musical
            </option>

          </select>

          {errors.tipo_proyecto && (
            <p>
              {errors.tipo_proyecto.message}
            </p>
          )}


          <label>
            Integrantes / alias
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("integrantes")}
          />


          <label>
            Año de inicio
          </label>

          <input
            type="number"
            min="1900"
            max="2100"
            autoComplete="off"
            {...register("anio_inicio")}
          />


          <label>
            País
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("pais", {
              required: "El país es obligatorio",
            })}
          />

          {errors.pais && (
            <p>
              {errors.pais.message}
            </p>
          )}


          <label>
            Ciudad
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("ciudad")}
          />

        </section>


        <section>

          <h2>
            Identidad musical
          </h2>


          <label>
            Géneros / estilos
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("generos", {
              required: "Ingresa al menos un género musical",
            })}
          />

          {errors.generos && (
            <p>
              {errors.generos.message}
            </p>
          )}


          <label>
            Biografía artística
          </label>

          <textarea
            rows="7"
            autoComplete="off"
            {...register("biografia", {
              required: "La biografía es obligatoria",

              minLength: {
                value: 10,
                message:
                  "La biografía debe contener al menos 10 caracteres",
              },
            })}
          />

          {errors.biografia && (
            <p>
              {errors.biografia.message}
            </p>
          )}

        </section>


        <section>

          <h2>
            Demo
          </h2>


          <label>
            Nombre de la canción / demo
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register("nombre_demo", {
              required: "El nombre del demo es obligatorio",
            })}
          />

          {errors.nombre_demo && (
            <p>
              {errors.nombre_demo.message}
            </p>
          )}

        </section>


        <section>

          <h2>
            Presencia digital
          </h2>


          <label>
            Spotify
          </label>

          <input
            type="url"
            autoComplete="off"
            {...register("spotify_url")}
          />


          <label>
            Instagram
          </label>

          <input
            type="url"
            autoComplete="off"
            {...register("instagram_url")}
          />

        </section>


        <section>

          <h2>
            Contacto
          </h2>


          <label>
            Correo de contacto
          </label>

          <label>
            Correo de contacto
          </label>

          <input
            type="email"
            autoComplete="off"
            {...register("correo_contacto", {
              required: "El correo es obligatorio",

              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
                message:
                  "Ingresa un correo válido, por ejemplo nombre@dominio.com",
              },
            })}
          />

          {errors.correo_contacto && (
            <p>
              {errors.correo_contacto.message}
            </p>
          )}


          <label>
            Mensaje para el sello
          </label>

          <textarea
            rows="5"
            autoComplete="off"
            {...register("mensaje_sello")}
          />

        </section>


        <section>

          <h2>
            Autorizaciones
          </h2>


          <label>

            <input
              type="checkbox"
              {...register("consentimiento_datos", {
                required:
                  "Debes aceptar el tratamiento de datos",
              })}
            />

            Acepto el tratamiento de mis datos personales.

          </label>

          {errors.consentimiento_datos && (
            <p>
              {errors.consentimiento_datos.message}
            </p>
          )}


          <label>

            <input
              type="checkbox"
              {...register("autorizacion_demo", {
                required:
                  "Debes autorizar el uso del demo",
              })}
            />

            Autorizo el uso del demo para recepción,
            almacenamiento y evaluación interna del sello.

          </label>

          {errors.autorizacion_demo && (
            <p>
              {errors.autorizacion_demo.message}
            </p>
          )}

        </section>


        {errorServidor && (
          <p className="postulacion-error-servidor">
            {errorServidor}
          </p>
        )}


        <button
          type="submit"
          className="primary-button postulacion-submit"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Enviando..."
            : "Enviar postulación"}
        </button>

      </form>

    </main>
  );
}


export default PostulacionPage;