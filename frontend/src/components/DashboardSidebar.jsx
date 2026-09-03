import logo from "../assets/forge-ar.svg";

function DashboardSidebar({ user, onLogout }) {
  const menuItems = [
    { label: "Resumen", icon: "◫", active: true },
    { label: "Postulaciones", icon: "♫" },
    { label: "Análisis", icon: "◇" },
    { label: "Reportes", icon: "▤" },
  ];

  return (
    <aside className="dashboard-sidebar">

      <div className="dashboard-sidebar-brand">
        <img
          src={logo}
          alt="Forge"
          className="dashboard-brand-logo"
        />

        <div>
          <strong>Forge</strong>
          <span>A&R</span>
        </div>
      </div>

      <nav className="dashboard-nav">
        {menuItems.map((item) => (
          <button
            key={item.label}
            type="button"
            className={`dashboard-nav-item ${
              item.active ? "active" : ""
            }`}
          >
            <span className="dashboard-nav-icon">
              {item.icon}
            </span>

            {item.label}
          </button>
        ))}
      </nav>

      <div className="dashboard-sidebar-bottom">

        <div className="dashboard-user-mini">

          <div className="dashboard-user-avatar">
            {user?.name?.charAt(0).toUpperCase()}
          </div>

          <div className="dashboard-user-mini-info">
            <strong>{user?.name}</strong>
            <span>A&R</span>
          </div>

        </div>

        <button
          type="button"
          className="dashboard-logout"
          onClick={onLogout}
        >
          Cerrar sesión
        </button>

      </div>

    </aside>
  );
}

export default DashboardSidebar;