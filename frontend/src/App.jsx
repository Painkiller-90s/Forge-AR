import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/NavBar";
import Footer from "./components/Footer";

import HomePage from "./pages/HomePage";
import ComoFuncionaPage from "./pages/ComoFuncionaPage";
import LoginPage from "./pages/LoginPage";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/Como funciona" element={<ComoFuncionaPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>

      <Footer />
    </BrowserRouter>
  );
}

export default App;