// components/FeatureCard.js
import React from "react";

function FeatureCard({ title, description, available, comingSoon, icon, onClick }) {
  return (
    <div className="feature-card">
      <div className="feature-card-header">
        <div className="feature-title">
          <span className="feature-icon">{icon}</span>
          <span className="feature-name">{title}</span>
        </div>
        {comingSoon && <span className="coming-soon">Coming Soon</span>}
      </div>
      <div className="feature-card-body">
        <p>{description}</p>
        {available ? (
          <button className="feature-button available" onClick={onClick || (() => {})}>
            Access Now
          </button>
        ) : (
          <button className="feature-button disabled" disabled>
            Notify Me
          </button>
        )}
      </div>
    </div>
  );
}

export default FeatureCard;
