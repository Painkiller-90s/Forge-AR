import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/NavBar";
import Footer from "./components/Footer";

import HomePage from "./pages/HomePage";
import PlataformaPage from "./pages/PlataformaPage";
import FuncionesPage from "./pages/FuncionesPage";
import LoginPage from "./pages/LoginPage";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/plataforma" element={<PlataformaPage />} />
        <Route path="/funciones" element={<FuncionesPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>

      <Footer />
    </BrowserRouter>
  );
}

export default App;