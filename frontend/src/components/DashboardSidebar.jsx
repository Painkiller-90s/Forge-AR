
import logo from "../assets/forge-ar.svg";

function DashboardSidebar({
  user,
  onLogout,
  activeView,
  onNavigate,
}) {
  const menuItems = [
    { id: "resumen", label: "Resumen", icon: "◫" },
    { id: "postulaciones", label: "Postulaciones", icon: "♫" },
    { id: "analisis", label: "Análisis", icon: "◇", disabled: true },
    { id: "reportes", label: "Reportes", icon: "▤", disabled: true },
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
            key={item.id}
            type="button"
            disabled={item.disabled}
            onClick={() => onNavigate(item.id)}
            className={`dashboard-nav-item ${
              activeView === item.id ? "active" : ""
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
            {user?.name?.charAt(0)?.toUpperCase() || "A"}
          </div>

          <div className="dashboard-user-mini-info">
            <strong>{user?.name || "Usuario"}</strong>
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
