import { useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axios";
import "../styles/AccesoAR.css";


function AccesoAR() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      /* =========================
         LOGIN
      ========================= */

      const response = await api.post("/auth/login", {
        email,
        password,
      });

      const token = response.data.access_token;


      /* =========================
         GUARDAR TOKEN
      ========================= */

      sessionStorage.setItem("access_token", token);


      /* =========================
         OBTENER USUARIO
      ========================= */

      const userResponse = await api.get("/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const user = userResponse.data;

      console.log("Usuario autenticado:", user);


      /* =========================
         REDIRECCIÓN POR ROL
      ========================= */

      if (user.role === "ar") {
        navigate("/dashboard");
        return;
      }

      if (user.role === "admin") {
        navigate("/admin");
        return;
      }


      /* =========================
         ROL NO VÁLIDO
      ========================= */

      sessionStorage.removeItem("access_token");

      setError(
        "Tu cuenta no posee un rol válido para acceder al sistema."
      );

    } catch (error) {
      console.error("Error al iniciar sesión:", error);

      sessionStorage.removeItem("access_token");

      if (error.response?.status === 401) {
        setError(
          "Correo o contraseña incorrectos. Por favor, verifica tus credenciales y vuelve a intentarlo."
        );

      } else if (error.response?.status === 403) {
        setError(
          "Tu usuario se encuentra desactivado."
        );

      } else if (error.response?.status === 422) {
        setError(
          "Los datos ingresados no son válidos."
        );

      } else {
        setError(
          "No fue posible iniciar sesión. Inténtalo nuevamente."
        );
      }

    } finally {
      setLoading(false);
    }
  };


  return (
    <main className="acceso-ar-page">

      <section className="acceso-ar-container">

        <div className="acceso-ar-card">

          {/* =========================
              HEADER
          ========================= */}

          <div className="acceso-ar-card-header">

            <span className="acceso-ar-card-label">
              ACCESO A&R
            </span>

            <h2>
              Bienvenido de vuelta
            </h2>

            <p>
              Ingresa tus credenciales para acceder al panel.
            </p>

          </div>


          {/* =========================
              FORMULARIO
          ========================= */}

          <form
            className="acceso-ar-form"
            onSubmit={handleSubmit}
          >

            {/* CORREO */}

            <div className="acceso-ar-field">

              <label htmlFor="email">
                Correo electrónico
              </label>

              <div className="acceso-ar-input">

                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="nombre@dominio.com"
                  autoComplete="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  disabled={loading}
                  required
                />

              </div>

            </div>


            {/* CONTRASEÑA */}

            <div className="acceso-ar-field">

              <label htmlFor="password">
                Contraseña
              </label>

              <div className="acceso-ar-input">

                <input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Contraseña"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  disabled={loading}
                  required
                />

              </div>

            </div>


            {/* ERROR */}

            {error && (
              <p className="acceso-ar-error">
                {error}
              </p>
            )}


            {/* BOTÓN */}

            <button
              type="submit"
              className="primary-button acceso-ar-submit"
              disabled={loading}
            >
              {loading
                ? "Iniciando sesión..."
                : "Iniciar sesión"}
            </button>

          </form>

        </div>

      </section>

    </main>
  );
}


export default AccesoAR;