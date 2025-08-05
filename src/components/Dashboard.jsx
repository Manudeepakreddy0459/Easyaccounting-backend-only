// components/Dashboard.js
import React, { useState } from "react";
import FeatureCard from "./FeatureCard.jsx";
import AutoLedger from "./AutoLedger.jsx";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [showAutoLedger, setShowAutoLedger] = useState(false);

  const stats = [
    {
      title: "Total Clients",
      value: "247",
      change: "+12%",
      changeType: "positive",
      icon: "👥",
    },
    {
      title: "Active Projects",
      value: "89",
      change: "+5%",
      changeType: "positive",
      icon: "📊",
    },
    {
      title: "Pending Returns",
      value: "23",
      change: "-8%",
      changeType: "negative",
      icon: "📋",
    },
    {
      title: "Revenue (₹)",
      value: "2.4M",
      change: "+18%",
      changeType: "positive",
      icon: "💰",
    },
  ];

  const recentActivities = [
    {
      id: 1,
      type: "GST Filing",
      client: "ABC Enterprises",
      status: "Completed",
      time: "2 hours ago",
      icon: "✅",
    },
    {
      id: 2,
      type: "TDS Return",
      client: "XYZ Corp",
      status: "Pending",
      time: "4 hours ago",
      icon: "⏳",
    },
    {
      id: 3,
      type: "Audit Report",
      client: "DEF Ltd",
      status: "In Progress",
      time: "1 day ago",
      icon: "📝",
    },
    {
      id: 4,
      type: "Tax Planning",
      client: "GHI Solutions",
      status: "Completed",
      time: "2 days ago",
      icon: "✅",
    },
  ];

  const quickActions = [
    {
      title: "New Client",
      description: "Add a new client to your database",
      icon: "➕",
      action: "add-client",
      available: true,
    },
    {
      title: "GST Filing",
      description: "File GST returns for clients",
      icon: "📄",
      action: "gst-filing",
      available: true,
    },
    {
      title: "TDS Return",
      description: "Prepare and submit TDS returns",
      icon: "📋",
      action: "tds-return",
      available: true,
    },
    {
      title: "Audit Report",
      description: "Generate audit reports",
      icon: "📊",
      action: "audit-report",
      available: false,
    },
  ];

  const features = [
    {
      title: "Auto Ledger",
      description: "Generate journal entries from bank statements automatically",
      available: true,
      comingSoon: false,
      icon: "🏦",
      onClick: () => setShowAutoLedger(true),
    },
    {
      title: "Journal Entries",
      description: "View and manage all journal entries with smart categorization",
      available: false,
      comingSoon: true,
      icon: "📝",
    },
    {
      title: "Ledger View",
      description: "Comprehensive ledger account views with drill-down capabilities",
      available: false,
      comingSoon: true,
      icon: "📊",
    },
    {
      title: "Profit & Loss",
      description: "Generate and analyze P&L statements with trend analysis",
      available: false,
      comingSoon: true,
      icon: "📈",
    },
    {
      title: "Balance Sheet",
      description: "View and export balance sheets with comparative analysis",
      available: false,
      comingSoon: true,
      icon: "⚖️",
    },
    {
      title: "GST Filing",
      description: "Prepare and submit GST returns with auto-validation",
      available: false,
      comingSoon: true,
      icon: "🏛️",
    },
    {
      title: "TDS Filing",
      description: "Manage TDS calculations and filing with compliance checks",
      available: false,
      comingSoon: true,
      icon: "📋",
    },
    {
      title: "Client Database",
      description: "Organize and access client information with secure storage",
      available: false,
      comingSoon: true,
      icon: "👥",
    },
    {
      title: "Push to Tally",
      description: "Push data to Tally seamlessly with real-time sync",
      available: false,
      comingSoon: true,
      icon: "🔄",
    },
    {
      title: "Compliance Alerts",
      description: "Get compliance reminders and alerts for all deadlines",
      available: false,
      comingSoon: true,
      icon: "🔔",
    },
  ];

  // If AutoLedger is active, show it instead of dashboard
  if (showAutoLedger) {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <div className="header-left">
            <button 
              className="back-button"
              onClick={() => setShowAutoLedger(false)}
            >
              ← Back to Dashboard
            </button>
          </div>
        </header>
        <AutoLedger onBackToDashboard={() => setShowAutoLedger(false)} />
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>CA Assistant AI</h1>
          <p>Professional Accounting Dashboard</p>
        </div>
        <div className="header-right">
          <div className="user-info">
            <span className="user-avatar">👨‍💼</span>
            <span className="user-name">CA Manudeep</span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="dashboard-nav">
        <button
          className={`nav-tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📊 Overview
        </button>
        <button
          className={`nav-tab ${activeTab === "clients" ? "active" : ""}`}
          onClick={() => setActiveTab("clients")}
        >
          👥 Clients
        </button>
        <button
          className={`nav-tab ${activeTab === "compliance" ? "active" : ""}`}
          onClick={() => setActiveTab("compliance")}
        >
          📋 Compliance
        </button>
        <button
          className={`nav-tab ${activeTab === "reports" ? "active" : ""}`}
          onClick={() => setActiveTab("reports")}
        >
          📈 Reports
        </button>
      </nav>

      {/* Main Content */}
      <main className="dashboard-main">
        {activeTab === "overview" && (
          <>
            {/* Statistics Cards */}
            <section className="stats-section">
              <h2>Key Metrics</h2>
              <div className="stats-grid">
                {stats.map((stat, index) => (
                  <div key={index} className="stat-card">
                    <div className="stat-icon">{stat.icon}</div>
                    <div className="stat-content">
                      <h3>{stat.title}</h3>
                      <div className="stat-value">{stat.value}</div>
                      <div className={`stat-change ${stat.changeType}`}>
                        {stat.change}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Quick Actions */}
            <section className="quick-actions-section">
              <h2>Quick Actions</h2>
              <div className="quick-actions-grid">
                {quickActions.map((action, index) => (
                  <div key={index} className="quick-action-card">
                    <div className="action-icon">{action.icon}</div>
                    <h3>{action.title}</h3>
                    <p>{action.description}</p>
                    <button
                      className={`action-button ${!action.available ? "disabled" : ""}`}
                      disabled={!action.available}
                    >
                      {action.available ? "Start" : "Coming Soon"}
                    </button>
                  </div>
                ))}
              </div>
            </section>

            {/* Recent Activities */}
            <section className="recent-activities-section">
              <h2>Recent Activities</h2>
              <div className="activities-list">
                {recentActivities.map((activity) => (
                  <div key={activity.id} className="activity-item">
                    <div className="activity-icon">{activity.icon}</div>
                    <div className="activity-content">
                      <h4>{activity.type}</h4>
                      <p>{activity.client}</p>
                    </div>
                    <div className="activity-status">
                      <span className={`status-badge ${activity.status.toLowerCase()}`}>
                        {activity.status}
                      </span>
                      <span className="activity-time">{activity.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {activeTab === "clients" && (
          <section className="clients-section">
            <h2>Client Management</h2>
            <p>Client management features coming soon...</p>
          </section>
        )}

        {activeTab === "compliance" && (
          <section className="compliance-section">
            <h2>Compliance Dashboard</h2>
            <p>Compliance tracking features coming soon...</p>
          </section>
        )}

        {activeTab === "reports" && (
          <section className="reports-section">
            <h2>Reports & Analytics</h2>
            <p>Reporting features coming soon...</p>
          </section>
        )}
      </main>

      {/* Features Grid */}
      <section className="features-section">
        <h2>Available Features</h2>
        <div className="feature-grid">
          {features.map((feature, idx) => (
            <FeatureCard key={idx} {...feature} />
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
