import { NavLink } from "react-router-dom";
import "../styles/NavBar.css";
import logo from "../assets/forge-ar.svg";


function Navbar() {
  return (
    <header className="navbar">

      <NavLink className="brand" to="/">
        <img src={logo} alt="Forge A&R" className="brand-logo" />
        <span>FORGE A&R</span>
      </NavLink>

      <nav className="nav-links">

        <NavLink to="/" className={({ isActive }) => (isActive ? "active" : "")}>
          Inicio
        </NavLink>

        <NavLink to="/plataforma" className={({ isActive }) => (isActive ? "active" : "")}>
          Plataforma
        </NavLink>

        <NavLink to="/funciones" className={({ isActive }) => (isActive ? "active" : "")}>
          Funciones
        </NavLink>

      </nav>

      <NavLink className="login-button" to="/login">
        Iniciar sesión
      </NavLink>

    </header>
  );
}

export default Navbar;