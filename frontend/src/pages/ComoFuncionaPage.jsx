import { Link } from "react-router-dom";

import {
  UserRound,
  Music2,
  Upload,
  Send,
  Clock3,
  UsersRound,
  FileSearch,
  AudioLines,
  BarChart3,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";

import "../styles/ComoFuncionaPage.css";


function ComoFuncionaPage() {
  return (
    <div className="como-funciona-page">

      {/* =========================
          HERO
      ========================= */}

      <section className="how-hero">

        <span className="how-eyebrow">
          CÓMO FUNCIONA
        </span>

        <h1>
          Una plataforma.
          <span>Dos experiencias.</span>
        </h1>

        <p>
          Forge A&R conecta a artistas y equipos A&R dentro de un
          mismo flujo, centralizando postulaciones, demos, métricas
          y evaluaciones.
        </p>

      </section>


      {/* =========================
          ARTISTAS
      ========================= */}

      <section className="user-flow artist-flow">

        <div className="flow-header">

          <div className="flow-icon">
            <UserRound size={25} />
          </div>

          <div>
            <span className="flow-label">
              PARA ARTISTAS
            </span>

            <h2>
              Postula tu proyecto.
            </h2>

            <p>
              El artista puede presentar su proyecto musical desde
              un único lugar y seguir el estado de su postulación.
            </p>
          </div>

        </div>


        <div className="steps-grid artist-steps">

          <article className="step-card">

            <span className="step-number">
              01
            </span>

            <Music2 size={24} />

            <h3>Crear perfil</h3>

            <p>
              Registra la información principal del artista o banda.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              02
            </span>

            <UserRound size={24} />

            <h3>Completar proyecto</h3>

            <p>
              Añade información musical, enlaces y datos relevantes.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              03
            </span>

            <Upload size={24} />

            <h3>Subir demo</h3>

            <p>
              Adjunta el material musical que será revisado por el sello.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              04
            </span>

            <Send size={24} />

            <h3>Enviar postulación</h3>

            <p>
              Envía el proyecto completo para iniciar el proceso de evaluación.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              05
            </span>

            <Clock3 size={24} />

            <h3>Consultar estado</h3>

            <p>
              Revisa el avance y estado actual de la postulación.
            </p>

          </article>

        </div>

      </section>


      {/* =========================
          CONEXIÓN
      ========================= */}

      <section className="connection-section">

        <div className="connection-heading">

          <span>
            UN MISMO FLUJO
          </span>

          <h2>
            Forge A&R conecta ambos lados del proceso.
          </h2>

          <p>
            La información enviada por el artista se organiza y transforma
            en un entorno de evaluación para el equipo A&R.
          </p>

        </div>


        <div className="connection-flow">

          <div className="connection-node">

            <UserRound size={28} />

            <div>
              <span>ARTISTA</span>
              <strong>Postulación</strong>
            </div>

          </div>


          <ArrowRight
            className="connection-arrow"
            size={28}
          />


          <div className="forge-node">

            <span className="forge-node-title">
              FORGE A&R
            </span>

            <div className="forge-data-list">

              <span>
                <CheckCircle2 size={15} />
                Información
              </span>

              <span>
                <CheckCircle2 size={15} />
                Demos
              </span>

              <span>
                <CheckCircle2 size={15} />
                Métricas
              </span>

              <span>
                <CheckCircle2 size={15} />
                Evaluaciones
              </span>

            </div>

          </div>


          <ArrowRight
            className="connection-arrow"
            size={28}
          />


          <div className="connection-node">

            <UsersRound size={28} />

            <div>
              <span>EQUIPO A&R</span>
              <strong>Evaluación</strong>
            </div>

          </div>

        </div>

      </section>


      {/* =========================
          EQUIPO A&R
      ========================= */}

      <section className="user-flow ar-flow">

        <div className="flow-header">

          <div className="flow-icon">
            <UsersRound size={25} />
          </div>

          <div>
            <span className="flow-label">
              PARA EQUIPOS A&R
            </span>

            <h2>
              Evalúa con mayor contexto.
            </h2>

            <p>
              El equipo A&R recibe toda la información necesaria para
              revisar artistas, analizar sus demos y registrar una decisión.
            </p>
          </div>

        </div>


        <div className="steps-grid ar-steps">

          <article className="step-card">

            <span className="step-number">
              01
            </span>

            <FileSearch size={24} />

            <h3>Recibir postulaciones</h3>

            <p>
              Accede a los proyectos enviados por los artistas.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              02
            </span>

            <UserRound size={24} />

            <h3>Revisar artista</h3>

            <p>
              Consulta el perfil, información musical y enlaces asociados.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              03
            </span>

            <AudioLines size={24} />

            <h3>Validar demo</h3>

            <p>
              Revisa los resultados técnicos obtenidos del material enviado.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              04
            </span>

            <BarChart3 size={24} />

            <h3>Consultar métricas</h3>

            <p>
              Analiza información externa asociada al proyecto artístico.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              05
            </span>

            <ShieldCheck size={24} />

            <h3>Analizar riesgo</h3>

            <p>
              Utiliza los indicadores disponibles como apoyo a la evaluación.
            </p>

          </article>


          <article className="step-card">

            <span className="step-number">
              06
            </span>

            <CheckCircle2 size={24} />

            <h3>Registrar decisión</h3>

            <p>
              Guarda la evaluación final y mantiene la trazabilidad del proceso.
            </p>

          </article>

        </div>

      </section>


      {/* =========================
          CTA
      ========================= */}

      <section className="how-cta">

        <div>

          <span>
            FORGE A&R
          </span>

          <h2>
            Un proceso más ordenado para ambas partes.
          </h2>

          <p>
            Desde la postulación del artista hasta la evaluación
            final del equipo A&R.
          </p>

        </div>

        <Link
          to="/login"
          className="primary-button"
        >
          Iniciar sesión
          <ArrowRight size={18} />
        </Link>

      </section>

    </div>
  );
}

export default ComoFuncionaPage;