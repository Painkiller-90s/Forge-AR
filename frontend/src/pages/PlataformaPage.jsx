import {
  Upload,
  AudioLines,
  BarChart3,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

import "../styles/PlataformaPage.css";

function PlataformaPage() {
  return (
    <div className="plataforma-page">

      {/* =========================
          HERO
      ========================= */}
      <section className="platform-hero">

        <div className="platform-hero-content">

          <span className="platform-eyebrow">
            PLATAFORMA FORGE A&R
          </span>

          <h1>
            Un proceso A&R
            <span>más claro y trazable.</span>
          </h1>

          <p>
            Centraliza postulaciones, analiza demos y reúne métricas
            relevantes en un solo lugar para apoyar la evaluación
            de nuevos artistas.
          </p>

        </div>

        <div className="platform-preview">

          <div className="preview-header">
            <span>FORGE A&R</span>

            <span className="preview-status">
              EVALUACIÓN
            </span>
          </div>

          <div className="preview-content">

            <div className="preview-row">
              <span>Demo recibido</span>
              <CheckCircle2 size={17} />
            </div>

            <div className="preview-row">
              <span>Validación técnica</span>
              <CheckCircle2 size={17} />
            </div>

            <div className="preview-row">
              <span>Métricas externas</span>
              <CheckCircle2 size={17} />
            </div>

            <div className="preview-row">
              <span>Análisis de riesgo</span>
              <span className="preview-processing">
                En análisis
              </span>
            </div>

          </div>

        </div>

      </section>


      {/* =========================
          PROCESO
      ========================= */}
      <section className="platform-process">

        <div className="platform-section-heading">

          <span>FLUJO DE TRABAJO</span>

          <h2>
            Del demo a una decisión informada.
          </h2>

          <p>
            Forge A&R organiza las distintas etapas del proceso
            de evaluación para reducir tareas manuales y mejorar
            la trazabilidad.
          </p>

        </div>

        <div className="process-grid">

          <article className="process-card">

            <div className="process-number">01</div>

            <Upload size={26} />

            <h3>Recepción</h3>

            <p>
              Los artistas envían su información y material
              directamente a través de la plataforma.
            </p>

          </article>


          <article className="process-card">

            <div className="process-number">02</div>

            <AudioLines size={26} />

            <h3>Validación</h3>

            <p>
              El sistema revisa características técnicas del
              audio y organiza los demos recibidos.
            </p>

          </article>


          <article className="process-card">

            <div className="process-number">03</div>

            <BarChart3 size={26} />

            <h3>Métricas</h3>

            <p>
              Se reúnen datos relevantes que permiten observar
              el alcance y evolución del proyecto artístico.
            </p>

          </article>


          <article className="process-card">

            <div className="process-number">04</div>

            <ShieldCheck size={26} />

            <h3>Evaluación</h3>

            <p>
              La información obtenida apoya el análisis de riesgo
              y la decisión final del equipo A&R.
            </p>

          </article>

        </div>

      </section>


      {/* =========================
          INFORMACIÓN
      ========================= */}
      <section className="platform-info">

        <div className="platform-info-content">

          <span className="platform-eyebrow">
            INFORMACIÓN CENTRALIZADA
          </span>

          <h2>
            Todo lo necesario para evaluar un proyecto.
          </h2>

          <p>
            Cada postulación mantiene asociada la información
            necesaria para que el equipo pueda revisar y comparar
            artistas desde un mismo entorno.
          </p>

          <ul>
            <li>
              <CheckCircle2 size={18} />
              Información del artista y proyecto musical.
            </li>

            <li>
              <CheckCircle2 size={18} />
              Archivos y validación técnica de demos.
            </li>

            <li>
              <CheckCircle2 size={18} />
              Métricas externas relevantes.
            </li>

            <li>
              <CheckCircle2 size={18} />
              Historial y trazabilidad de evaluaciones.
            </li>
          </ul>

        </div>

        <div className="platform-data-panel">

          <div className="data-panel-header">
            <span>POSTULACIÓN</span>
            <span>#0248</span>
          </div>

          <div className="data-item">
            <span>Estado</span>
            <strong>En evaluación</strong>
          </div>

          <div className="data-item">
            <span>Demo</span>
            <strong>Validado</strong>
          </div>

          <div className="data-item">
            <span>Métricas</span>
            <strong>Disponibles</strong>
          </div>

          <div className="data-item">
            <span>Riesgo</span>
            <strong className="risk-medium">
              Moderado
            </strong>
          </div>

        </div>

      </section>


      {/* =========================
          CTA
      ========================= */}
      <section className="platform-cta">

        <div>
          <span>FORGE A&R</span>

          <h2>
            Convierte información en mejores decisiones.
          </h2>

          <p>
            Una plataforma diseñada para apoyar el proceso de
            descubrimiento y evaluación de nuevos artistas.
          </p>
        </div>

        <button className="primary-button">
          Iniciar sesión
          <ArrowRight size={18} />
        </button>

      </section>

    </div>
  );
}

export default PlataformaPage;