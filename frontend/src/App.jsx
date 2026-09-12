import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

import HomePage from "./pages/HomePage";
import ComoFuncionaPage from "./pages/ComoFuncionaPage";
import AccesoAR from "./pages/AccesoAR";
import DashboardAR from "./pages/DashboardAR";


function AppContent() {
  const location = useLocation();

  const isDashboard =
    location.pathname.startsWith("/dashboard") ||
    location.pathname.startsWith("/admin");

  return (
    <>
      {!isDashboard && <Navbar />}

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
      </Routes>

      {!isDashboard && <Footer />}
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