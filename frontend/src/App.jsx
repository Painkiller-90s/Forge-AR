import { BrowserRouter, Routes, Route } from "react-router-dom";

import HomePage from "./pages/HomePage";
import PlataformaPage from "./pages/PlataformaPage";
import FuncionesPage from "./pages/FuncionesPage";
import LoginPage from "./pages/LoginPage";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/plataforma" element={<PlataformaPage />} />
        <Route path="/funciones" element={<FuncionesPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;