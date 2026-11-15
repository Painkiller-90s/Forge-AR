
import { useCallback, useEffect, useState } from "react";
import api from "../api/axios";
import "../styles/GestionUsuariosPanel.css";

function obtenerConfigAuth() {
  const token = sessionStorage.getItem("access_token");

  if (!token) {
    throw new Error("No existe una sesión activa. Vuelve a iniciar sesión.");
  }

  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
}

function obtenerMensajeError(error, mensajePredeterminado) {
  const detalle = error.response?.data?.detail;

  return (
    (typeof detalle === "string" ? detalle : null) ||
    error.message ||
    mensajePredeterminado
  );
}

function GestionUsuariosPanel() {
  const [usuarios, setUsuarios] = useState([]);
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");

  const [cargando, setCargando] = useState(true);
  const [creando, setCreando] = useState(false);
  const [actualizandoId, setActualizandoId] = useState(null);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  const cargarUsuarios = useCallback(async () => {
    setCargando(true);
    setError("");

    try {
      const respuesta = await api.get("/users/", obtenerConfigAuth());

      setUsuarios(
        Array.isArray(respuesta.data) ? respuesta.data : []
      );
    } catch (err) {
      setError(
        obtenerMensajeError(
          err,
          "No fue posible cargar los usuarios A&R."
        )
      );
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarUsuarios();
  }, [cargarUsuarios]);

  const handleCrearUsuario = async (event) => {
    event.preventDefault();

    setCreando(true);
    setError("");
    setMensaje("");

    try {
      await api.post(
        "/users/",
        {
          name: nombre.trim(),
          email: correo.trim().toLowerCase(),
          password: contrasena,
        },
        obtenerConfigAuth()
      );

      setNombre("");
      setCorreo("");
      setContrasena("");

      setMensaje("El usuario A&R fue creado correctamente.");

      await cargarUsuarios();
    } catch (err) {
      setError(
        obtenerMensajeError(
          err,
          "No fue posible crear el usuario A&R."
        )
      );
    } finally {
      setCreando(false);
    }
  };

  const handleCambiarEstado = async (usuario) => {
    const accion = usuario.is_active ? "desactivar" : "activar";

    const confirmado = window.confirm(
      `¿Seguro que deseas ${accion} la cuenta de ${usuario.name}?`
    );

    if (!confirmado) return;

    setActualizandoId(usuario.id);
    setError("");
    setMensaje("");

    try {
      await api.put(
        `/users/${usuario.id}`,
        {
          is_active: !usuario.is_active,
        },
        obtenerConfigAuth()
      );

      setMensaje(
        usuario.is_active
          ? "La cuenta A&R fue desactivada."
          : "La cuenta A&R fue reactivada."
      );

      await cargarUsuarios();
    } catch (err) {
      setError(
        obtenerMensajeError(
          err,
          "No fue posible actualizar el usuario."
        )
      );
    } finally {
      setActualizandoId(null);
    }
  };

  const usuariosActivos = usuarios.filter(
    (usuario) => usuario.is_active
  ).length;

  return (
    <section className="dashboard-panel users-dashboard">
      <header className="users-header">
        <div>
          <span className="dashboard-panel-label">
            GESTIÓN DEL EQUIPO
          </span>

          <h2>Usuarios A&R</h2>

          <p>
            Crea y administra las cuentas de los integrantes
            de tu sello discográfico.
          </p>
        </div>

        <div className="users-summary">
          <span>Usuarios activos</span>
          <strong>{usuariosActivos}</strong>
          <small>{usuarios.length} cuentas registradas</small>
        </div>
      </header>

      {mensaje && (
        <p
          className="users-feedback users-feedback-success"
          role="status"
        >
          {mensaje}
        </p>
      )}

      {error && (
        <p
          className="users-feedback users-feedback-error"
          role="alert"
        >
          {error}
        </p>
      )}

      <div className="users-layout">
        <form
          className="users-form"
          onSubmit={handleCrearUsuario}
        >
          <div className="users-section-heading">
            <h3>Crear usuario A&R</h3>
            <p>
              La cuenta quedará asociada automáticamente a tu sello.
            </p>
          </div>

          <label htmlFor="usuario-nombre">
            Nombre completo
          </label>

          <input
            id="usuario-nombre"
            type="text"
            value={nombre}
            onChange={(event) => setNombre(event.target.value)}
            placeholder="Ej. Juan Pérez"
            minLength={2}
            maxLength={100}
            autoComplete="name"
            required
          />

          <label htmlFor="usuario-correo">
            Correo electrónico
          </label>

          <input
            id="usuario-correo"
            type="email"
            value={correo}
            onChange={(event) => setCorreo(event.target.value)}
            placeholder="usuario@correo.com"
            autoComplete="email"
            required
          />

          <label htmlFor="usuario-contrasena">
            Contraseña inicial
          </label>

          <input
            id="usuario-contrasena"
            type="password"
            value={contrasena}
            onChange={(event) => setContrasena(event.target.value)}
            placeholder="Mínimo 8 caracteres"
            minLength={8}
            maxLength={128}
            autoComplete="new-password"
            required
          />

          <div className="users-role-note">
            <span aria-hidden="true">✓</span>

            <div>
              <strong>Rol A&R</strong>
              <small>
                El sello se asigna automáticamente.
              </small>
            </div>
          </div>

          <button
            type="submit"
            className="users-submit"
            disabled={creando}
          >
            {creando ? "Creando usuario..." : "Crear usuario A&R"}
          </button>
        </form>

        <div className="users-list-section">
          <div className="users-section-heading">
            <h3>Usuarios registrados</h3>
            <p>
              Solo se muestran las cuentas A&R de este sello.
            </p>
          </div>

          {cargando && (
            <p className="users-empty">
              Cargando usuarios...
            </p>
          )}

          {!cargando && !error && usuarios.length === 0 && (
            <p className="users-empty">
              Todavía no hay usuarios A&R registrados.
            </p>
          )}

          {!cargando && usuarios.length > 0 && (
            <div className="users-table-wrapper">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Correo electrónico</th>
                    <th>Estado</th>
                    <th>Acción</th>
                  </tr>
                </thead>

                <tbody>
                  {usuarios.map((usuario) => (
                    <tr key={usuario.id}>
                      <td className="users-name">
                        {usuario.name}
                      </td>

                      <td>{usuario.email}</td>

                      <td>
                        <span
                          className={`users-status ${
                            usuario.is_active
                              ? "active"
                              : "inactive"
                          }`}
                        >
                          {usuario.is_active
                            ? "Activo"
                            : "Desactivado"}
                        </span>
                      </td>

                      <td>
                        <button
                          type="button"
                          className={`users-action ${
                            usuario.is_active
                              ? "deactivate"
                              : "activate"
                          }`}
                          onClick={() =>
                            handleCambiarEstado(usuario)
                          }
                          disabled={
                            actualizandoId === usuario.id
                          }
                        >
                          {actualizandoId === usuario.id
                            ? "Actualizando..."
                            : usuario.is_active
                              ? "Desactivar"
                              : "Reactivar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default GestionUsuariosPanel;
