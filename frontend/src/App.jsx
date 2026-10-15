import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";

import Navbar from "./components/NavBar";
import Footer from "./components/Footer";

import HomePage from "./pages/HomePage";
import ComoFuncionaPage from "./pages/ComoFuncionaPage";
import AccesoAR from "./pages/AccesoAR";
import DashboardAR from "./pages/DashboardAR";
import PostulacionPage from "./pages/PostulacionPage";
import ProtectedRoute from "./components/ProtectedRoute";
import DashboardAdmin from "./pages/DashboardAdmin";


function AppContent() {
  const location = useLocation();

  const isDashboard =
    location.pathname.startsWith("/dashboard") ||
    location.pathname.startsWith("/admin");

  const isPostulacion =
    location.pathname.startsWith("/postulacion");

  return (
    <>
      {!isDashboard && (
        <Navbar soloLogo={isPostulacion} />
      )}

      <Routes>

        <Route
          path="/"
          element={<HomePage />}
        />

        <Route
          path="/como-funciona"
          element={<ComoFuncionaPage />}
        />

        <Route
          path="/acceso"
          element={<AccesoAR />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute requiredRole="ar">
              <DashboardAR />
            </ProtectedRoute>
          }
        />

        <Route
          path="/postulacion/:selloId"
          element={<PostulacionPage />}
        />

        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <DashboardAdmin />
            </ProtectedRoute>
          }
        />

      </Routes>

      {!isDashboard && !isPostulacion && (
        <Footer />
      )}
    </>
  );
}


function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}


export default App;