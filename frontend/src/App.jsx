import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/NavBar";
import Footer from "./components/Footer";

import HomePage from "./pages/HomePage";
import ComoFuncionaPage from "./pages/ComoFuncionaPage";
import AccesoAR from "./pages/AccesoAR";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/como-funciona" element={<ComoFuncionaPage />} />
        <Route path="/acceso" element={<AccesoAR />} />
      </Routes>

      <Footer />
    </BrowserRouter>
  );
}

export default App;