import { useState } from "react";
import { useParams } from "react-router-dom";
import { useForm } from "react-hook-form";

import api from "../api/axios";

import "../styles/PostulacionPage.css";


function PostulacionPage() {
  const { selloId } = useParams();

  const [enviada, setEnviada] = useState(false);
  const [errorServidor, setErrorServidor] = useState("");

  const [demos, setDemos] = useState([
    {
      id: 1,
      nombre: "",
      archivo: null,
    },
  ]);

  const [errorDemos, setErrorDemos] = useState("");


  const {
    register,
    handleSubmit,
    formState: {
      errors,
      isSubmitting,
    },
  } = useForm();


  // =========================
  // CONFIGURACIÓN DEMOS
  // =========================

  const MAX_FILE_SIZE = 200 * 1024 * 1024;


  // =========================
  // ACTUALIZAR NOMBRE DEMO
  // =========================

  const actualizarNombreDemo = (id, nombre) => {
    setDemos((actuales) =>
      actuales.map((demo) =>
        demo.id === id
          ? {
              ...demo,
              nombre,
            }
          : demo
      )
    );

    setErrorDemos("");
  };


  // =========================
  // ACTUALIZAR ARCHIVO DEMO
  // =========================

  const actualizarArchivoDemo = (id, event) => {
    const archivo = event.target.files?.[0];

    if (!archivo) {
      return;
    }

    const extension = archivo.name
      .split(".")
      .pop()
      ?.toLowerCase();


    if (!["mp3", "flac"].includes(extension)) {
      setErrorDemos(
        "Solo se permiten archivos MP3 o FLAC."
      );

      event.target.value = "";

      return;
    }


    if (archivo.size > MAX_FILE_SIZE) {
      setErrorDemos(
        "Cada archivo puede pesar como máximo 200 MB."
      );

      event.target.value = "";

      return;
    }


    setDemos((actuales) =>
      actuales.map((demo) =>
        demo.id === id
          ? {
              ...demo,
              archivo,
            }
          : demo
      )
    );

    setErrorDemos("");
  };


  // =========================
  // AGREGAR DEMO
  // =========================

  const agregarDemo = () => {
    if (demos.length >= 3) {
      return;
    }

    const nuevoId =
      Math.max(
        ...demos.map((demo) => demo.id)
      ) + 1;

    setDemos((actuales) => [
      ...actuales,
      {
        id: nuevoId,
        nombre: "",
        archivo: null,
      },
    ]);

    setErrorDemos("");
  };


  // =========================
  // ELIMINAR DEMO
  // =========================

  const eliminarDemo = (id) => {
    if (demos.length === 1) {
      return;
    }

    setDemos((actuales) =>
      actuales.filter(
        (demo) => demo.id !== id
      )
    );

    setErrorDemos("");
  };


  // =========================
  // FORMATEAR TAMAÑO
  // =========================

  const formatearTamano = (bytes) => {
    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(2)} MB`;
  };


  // =========================
  // ENVIAR POSTULACIÓN
  // =========================

  const onSubmit = async (data) => {
    setErrorServidor("");
    setErrorDemos("");


    // Validar demos antes de enviar
    const demosInvalidas = demos.some(
      (demo) =>
        !demo.nombre.trim() ||
        !demo.archivo
    );


    if (demosInvalidas) {
      setErrorDemos(
        "Completa el nombre y selecciona un archivo para cada canción."
      );

      return;
    }


    // =========================
    // DATOS POSTULACIÓN
    // =========================

    const payload = {
      nombre_artistico:
        data.nombre_artistico,

      correo_contacto:
        data.correo_contacto,

      pais:
        data.pais,

      tipo_proyecto:
        data.tipo_proyecto,

      generos: data.generos
        .split(",")
        .map(
          (genero) =>
            genero.trim()
        )
        .filter(Boolean),

      biografia:
        data.biografia,

      demos: demos.map((demo) => ({
        nombre:
          demo.nombre.trim(),
      })),

      integrantes:
        data.integrantes
          ? data.integrantes
              .split(",")
              .map(
                (integrante) =>
                  integrante.trim()
              )
              .filter(Boolean)
          : [],

      ciudad:
        data.ciudad || null,

      anio_inicio:
        data.anio_inicio
          ? Number(data.anio_inicio)
          : null,

      spotify_url:
        data.spotify_url || null,

      instagram_url:
        data.instagram_url || null,

      mensaje_sello:
        data.mensaje_sello || null,

      consentimiento_datos:
        data.consentimiento_datos,

      autorizacion_demo:
        data.autorizacion_demo,
    };


    // =========================
    // FORMDATA
    // =========================

    const formData =
      new FormData();


    formData.append(
      "postulacion",
      JSON.stringify(payload)
    );


    demos.forEach((demo) => {
      formData.append(
        "archivos",
        demo.archivo
      );
    });


    // =========================
    // PETICIÓN
    // =========================

    try {
      await api.post(
        `/postulaciones/${selloId}`,
        formData
      );

      setEnviada(true);

    } catch (error) {
      console.error(error);

      const detalle =
        error.response?.data?.detail;


      if (typeof detalle === "string") {
        setErrorServidor(detalle);

      } else {
        setErrorServidor(
          "No se pudo enviar la postulación. Intenta nuevamente."
        );
      }
    }
  };


  // =========================
  // POSTULACIÓN ENVIADA
  // =========================

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


  // =========================
  // FORMULARIO
  // =========================

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


        {/* =========================
            INFORMACIÓN ARTÍSTICA
        ========================= */}

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
            {...register(
              "nombre_artistico",
              {
                required:
                  "El nombre artístico es obligatorio",

                minLength: {
                  value: 2,
                  message:
                    "Debe contener al menos 2 caracteres",
                },
              }
            )}
          />

          {errors.nombre_artistico && (
            <p>
              {
                errors
                  .nombre_artistico
                  .message
              }
            </p>
          )}


          <label>
            Tipo de proyecto
          </label>

          <select
            {...register(
              "tipo_proyecto",
              {
                required:
                  "Selecciona el tipo de proyecto",
              }
            )}
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
              {
                errors
                  .tipo_proyecto
                  .message
              }
            </p>
          )}


          <label>
            Integrantes / alias
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register(
              "integrantes"
            )}
          />


          <label>
            Año de inicio
          </label>

          <input
            type="number"
            min="1900"
            max="2100"
            autoComplete="off"
            {...register(
              "anio_inicio"
            )}
          />


          <label>
            País
          </label>

          <input
            type="text"
            autoComplete="off"
            {...register(
              "pais",
              {
                required:
                  "El país es obligatorio",
              }
            )}
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
            {...register(
              "ciudad"
            )}
          />

        </section>


        {/* =========================
            IDENTIDAD MUSICAL
        ========================= */}

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
            {...register(
              "generos",
              {
                required:
                  "Ingresa al menos un género musical",
              }
            )}
          />

          {errors.generos && (
            <p>
              {
                errors
                  .generos
                  .message
              }
            </p>
          )}


          <label>
            Biografía artística
          </label>

          <textarea
            rows="7"
            autoComplete="off"
            {...register(
              "biografia",
              {
                required:
                  "La biografía es obligatoria",

                minLength: {
                  value: 10,
                  message:
                    "La biografía debe contener al menos 10 caracteres",
                },
              }
            )}
          />

          {errors.biografia && (
            <p>
              {
                errors
                  .biografia
                  .message
              }
            </p>
          )}

        </section>


        {/* =========================
            DEMOS
        ========================= */}

        <section className="demos-section">

          <h2>
            Demos
          </h2>

          <p className="demos-intro">
            Puedes enviar entre 1 y 3 canciones en formato
            MP3 o FLAC.
          </p>


          {demos.map(
            (demo, index) => (

              <div
                className="demo-item"
                key={demo.id}
              >

                <div className="demo-item-header">

                  <h3>
                    Canción {index + 1}
                  </h3>

                  {demos.length > 1 && (
                    <button
                      type="button"
                      className="demo-remove-button"
                      onClick={() =>
                        eliminarDemo(
                          demo.id
                        )
                      }
                    >
                      Eliminar
                    </button>
                  )}

                </div>


                <label
                  htmlFor={
                    `demo-nombre-${demo.id}`
                  }
                >
                  Nombre de la canción / demo
                </label>

                <input
                  id={
                    `demo-nombre-${demo.id}`
                  }
                  type="text"
                  autoComplete="off"
                  value={demo.nombre}
                  onChange={(event) =>
                    actualizarNombreDemo(
                      demo.id,
                      event.target.value
                    )
                  }
                />


                <label
                  htmlFor={
                    `demo-archivo-${demo.id}`
                  }
                >
                  Archivo de audio
                </label>

                <input
                  id={
                    `demo-archivo-${demo.id}`
                  }
                  type="file"
                  accept=".mp3,.flac,audio/mpeg,audio/flac"
                  onChange={(event) =>
                    actualizarArchivoDemo(
                      demo.id,
                      event
                    )
                  }
                />


                {demo.archivo && (
                  <div className="demo-file-info">

                    <span>
                      {
                        demo
                          .archivo
                          .name
                      }
                    </span>

                    <span>
                      {
                        formatearTamano(
                          demo
                            .archivo
                            .size
                        )
                      }
                    </span>

                  </div>
                )}

              </div>

            )
          )}


          {errorDemos && (
            <p className="demo-error">
              {errorDemos}
            </p>
          )}


          {demos.length < 3 && (
            <button
              type="button"
              className="demo-add-button"
              onClick={
                agregarDemo
              }
            >
              + Agregar otra canción
            </button>
          )}


          <p className="demo-limit">
            Máximo 3 canciones · MP3 o FLAC · 200 MB por archivo
          </p>

        </section>


        {/* =========================
            PRESENCIA DIGITAL
        ========================= */}

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
            {...register(
              "spotify_url"
            )}
          />


          <label>
            Instagram
          </label>

          <input
            type="url"
            autoComplete="off"
            {...register(
              "instagram_url"
            )}
          />

        </section>


        {/* =========================
            CONTACTO
        ========================= */}

        <section>

          <h2>
            Contacto
          </h2>


          <label>
            Correo de contacto
          </label>

          <input
            type="email"
            autoComplete="off"
            {...register(
              "correo_contacto",
              {
                required:
                  "El correo es obligatorio",

                pattern: {
                  value:
                    /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,

                  message:
                    "Ingresa un correo válido, por ejemplo nombre@dominio.com",
                },
              }
            )}
          />

          {errors.correo_contacto && (
            <p>
              {
                errors
                  .correo_contacto
                  .message
              }
            </p>
          )}


          <label>
            Mensaje para el sello
          </label>

          <textarea
            rows="5"
            autoComplete="off"
            {...register(
              "mensaje_sello"
            )}
          />

        </section>


        {/* =========================
            AUTORIZACIONES
        ========================= */}

        <section>

          <h2>
            Autorizaciones
          </h2>


          <label>

            <input
              type="checkbox"
              {...register(
                "consentimiento_datos",
                {
                  required:
                    "Debes aceptar el tratamiento de datos",
                }
              )}
            />

            Autorizo el tratamiento de mis datos personales.

          </label>

          {errors.consentimiento_datos && (
            <p>
              {
                errors
                  .consentimiento_datos
                  .message
              }
            </p>
          )}


          <label>

            <input
              type="checkbox"
              {...register(
                "autorizacion_demo",
                {
                  required:
                    "Debes autorizar el uso del demo",
                }
              )}
            />

            Autorizo el uso del demo para recepción,
            almacenamiento, análisis técnico y evaluación
            interna del sello.

          </label>

          {errors.autorizacion_demo && (
            <p>
              {
                errors
                  .autorizacion_demo
                  .message
              }
            </p>
          )}

        </section>


        {/* =========================
            ERROR SERVIDOR
        ========================= */}

        {errorServidor && (
          <p className="postulacion-error-servidor">
            {errorServidor}
          </p>
        )}


        {/* =========================
            ENVIAR
        ========================= */}

        <button
          type="submit"
          className="primary-button postulacion-submit"
          disabled={isSubmitting}
        >
          {
            isSubmitting
              ? "Enviando..."
              : "Enviar postulación"
          }
        </button>

      </form>

    </main>
  );
}


export default PostulacionPage;