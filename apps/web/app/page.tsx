import React from "react";

export default function WeatherDashboard() {
  return (
    <main className="p-8 max-w-5xl mx-auto font-sans">
      <h1 className="text-3xl font-bold mb-2">Weather Forecast & Alert Dashboard</h1>
      <p className="text-gray-600 mb-6">Multi-city 7-day forecasts, rain/heat/wind/UV risk alerts, and visualizations.</p>
      <div className="border rounded-lg p-4 bg-white shadow-sm">
        <p className="text-sm text-gray-500">Connect to FastAPI endpoints <code>GET /locations</code> and <code>GET /alerts</code>.</p>
      </div>
    </main>
  );
}
