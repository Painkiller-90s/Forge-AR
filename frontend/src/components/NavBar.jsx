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
        
        <NavLink to="/Como funciona" className={({ isActive }) => (isActive ? "active" : "")}>
          Cómo funciona
        </NavLink>

      </nav>

      <NavLink className="login-button" to="/login">
        Iniciar sesión
      </NavLink>

    </header>
  );
}

export default Navbar;