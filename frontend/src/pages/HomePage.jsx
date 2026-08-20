import {
  ArrowRight,
  AudioLines,
  BarChart3,
  ShieldCheck,
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

    </div>
  );
}

export default HomePage;