import React from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import "./Dashboard.css";
import "./Navbar.css";
import OverviewPage from "./pages/OverviewPage";
import TrendsPage from "./pages/TrendsPage";
import ClaimsPage from "./pages/ClaimsPage";
import NarrativesPage from "./pages/NarrativesPage";

function AppContent() {
  const location = useLocation();

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <img src="/marvel.webp" alt="Marvel Logo" className="brandLogo" />
        </div>

        <nav className="navbar">
          <NavLink to="/" end className={({ isActive }) => "navBtn" + (isActive ? " navBtnActive" : "")}>
            Overview
          </NavLink>
          <NavLink to="/trends" className={({ isActive }) => "navBtn" + (isActive ? " navBtnActive" : "")}>
            Trends
          </NavLink>
          <NavLink to="/claims" className={({ isActive }) => "navBtn" + (isActive ? " navBtnActive" : "")}>
            Claims
          </NavLink>
          <NavLink to="/narratives" className={({ isActive }) => "navBtn" + (isActive ? " navBtnActive" : "")}>
            Narratives
          </NavLink>
        </nav>

        <div className="topbarRight">
          <div className="searchWrap">
            <span className="searchIcon">⌕</span>
            <input className="searchInput" placeholder="Search a film, channel, or keyword..." />
          </div>
          <div className="avatar">SA</div>
        </div>
      </header>

      <main className="container">
        <Routes location={location}>
  <Route path="/"           element={<OverviewPage key={location.pathname} />} />
  <Route path="/trends"     element={<TrendsPage key={location.pathname} />} />
  <Route path="/claims"     element={<ClaimsPage key={location.pathname} />} />
  <Route path="/narratives" element={<NarrativesPage key={location.pathname} />} />
</Routes>
      </main>
    </div>
  );
}

export default function Dashboard() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}