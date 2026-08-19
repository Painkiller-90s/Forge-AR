import "../styles/Navbar.css";

function Navbar() {
  return (
    <header className="navbar">

      <a className="brand" href="/">
        <span className="brand-symbol">||||</span>
        <span>FORGE A&R</span>
      </a>

      <nav className="nav-links">
        <a href="/">Inicio</a>
        <a href="#plataforma">Plataforma</a>
        <a href="#funciones">Funciones</a>
      </nav>

      <button className="login-button">
        Iniciar sesión
      </button>

    </header>
  );
}

export default Navbar;