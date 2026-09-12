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
          element={<DashboardAR />}
        />

        <Route
          path="/postulacion/:selloId"
          element={<PostulacionPage />}
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