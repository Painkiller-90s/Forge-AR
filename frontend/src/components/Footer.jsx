import "../styles/Footer.css";
import logo from "../assets/forge-ar.svg";

function Footer() {
  return (
    <footer className="footer">

      <div className="footer-brand">
        <img
          src={logo}
          alt="Forge A&R"
          className="footer-brand-logo"
        />

        <span>FORGE A&R</span>
      </div>

      <p>
        Plataforma de apoyo a la evaluación A&R para sellos de metal extremo.
      </p>

    </footer>
  );
}

export default Footer;