import {
  ArrowRight,
  AudioLines,
  BarChart3,
  ShieldCheck,
  Upload,
  CheckCircle2,
} from "lucide-react";

import "../styles/HomePage.css";

function HomePage() {
  return (
    <div className="home-page">

      {/* PORTADA */}
      <main className="hero" id="inicio">

        <div className="hero-content">

          <span className="eyebrow">
            A&R PARA SELLOS DE METAL EXTREMO
          </span>

          <h1>
            Descubre talento.
            <span>Decide con datos.</span>
          </h1>

          <p className="hero-description">
            Forge A&R centraliza postulaciones, valida demos
            y reúne información clave para apoyar el proceso
            de evaluación y fichaje de nuevos artistas.
          </p>

          <div className="hero-actions">

            <button className="primary-button">
              Conocer la plataforma
              <ArrowRight size={18} />
            </button>

            <button className="secondary-button">
              Iniciar sesión
            </button>

          </div>

        </div>

        {/* DETALLE VISUAL */}
        <div className="visual">

          <div className="visual-top">
            <span>FORGE A&R</span>

            <span className="status">
              SISTEMA A&R
            </span>
          </div>

          <div className="visual-center">

            <div className="visual-wave">
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>

            <p>
              Validación · Métricas · Riesgo
            </p>

          </div>

        </div>

      </main>

      {/* FUNCIONES */}
      <section className="features" id="funciones">

        <div className="feature">

          <AudioLines size={25} />

          <div>
            <h3>Validación de demos</h3>

            <p>
              Revisa aspectos técnicos del audio y centraliza
              el material enviado por los artistas.
            </p>
          </div>

        </div>

        <div className="feature">

          <BarChart3 size={25} />

          <div>
            <h3>Métricas relevantes</h3>

            <p>
              Reúne información externa que ayude a comprender
              el alcance y evolución de cada proyecto.
            </p>
          </div>

        </div>

        <div className="feature">

          <ShieldCheck size={25} />

          <div>
            <h3>Análisis de riesgo</h3>

            <p>
              Entrega información de apoyo para tomar decisiones
              A&R con mayor trazabilidad.
            </p>
          </div>

        </div>

      </section>
        {/* =========================
            FLUJO DE LA PLATAFORMA
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
                Se reúnen datos relevantes para observar el alcance
                y evolución del proyecto artístico.
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
              INFORMACIÓN CENTRALIZADA
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

    </div>
  );
}

export default HomePage;