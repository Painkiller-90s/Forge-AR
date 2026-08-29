import "../styles/AccesoAR.css";

function AccesoAR() {
  return (
    <main className="acceso-ar-page">
      <section className="acceso-ar-container">



        <div className="acceso-ar-card">
          <div className="acceso-ar-card-header">
            <span className="acceso-ar-card-label">
              ACCESO A&R
            </span>

            <h2>Bienvenido de vuelta</h2>

            <p>
              Ingresa tus credenciales para acceder al panel.
            </p>
          </div>

          <form className="acceso-ar-form">
            <div className="acceso-ar-field">
              <label>Correo electrónico</label>

              <div className="acceso-ar-input">
                <input
                  type="email"
                  placeholder="nombre@dominio.com"
                />
              </div>
            </div>

            <div className="acceso-ar-field">
              <label>Contraseña</label>

              <div className="acceso-ar-input">
                <input
                  type="password"
                  placeholder="Contraseña"
                />
              </div>
            </div>

            <button
              type="submit"
              className="primary-button acceso-ar-submit"
            >
              Iniciar sesión
            </button>
          </form>
        </div>

      </section>
    </main>
  );
}

export default AccesoAR;