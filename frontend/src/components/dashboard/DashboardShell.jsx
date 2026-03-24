"use client";

import React, { useState } from "react";
import "./Dashboard.css";
import "./Navbar.css";
import OverviewPage from "./OverviewPage";
import TrendsPage from "./TrendsPage";
import ClaimsPage from "./ClaimsPage";
import NarrativesPage from "./NarrativesPage";

export default function DashboardShell() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <img src="/marvel.webp" alt="Marvel Logo" className="brandLogo" />
        </div>

        <nav className="navbar">
          <button
            className={"navBtn" + (activeTab === "overview" ? " navBtnActive" : "")}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>
          <button
            className={"navBtn" + (activeTab === "trends" ? " navBtnActive" : "")}
            onClick={() => setActiveTab("trends")}
          >
            Trends
          </button>
          <button
            className={"navBtn" + (activeTab === "claims" ? " navBtnActive" : "")}
            onClick={() => setActiveTab("claims")}
          >
            Claims
          </button>
          <button
            className={"navBtn" + (activeTab === "narratives" ? " navBtnActive" : "")}
            onClick={() => setActiveTab("narratives")}
          >
            Narratives
          </button>
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
        {activeTab === "overview" && <OverviewPage />}
        {activeTab === "trends" && <TrendsPage />}
        {activeTab === "claims" && <ClaimsPage />}
        {activeTab === "narratives" && <NarrativesPage />}
      </main>
    </div>
  );
}