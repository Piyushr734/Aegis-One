"use client";
import { useEffect, useState } from "react";
export default function Home() {
    const [events, setEvents] = useState<any[]>([]);

    useEffect(() => {
    fetch("http://127.0.0.1:8000/events")
      .then((response) => response.json())
      .then((data) => {
        setEvents(data.events);
      })
      .catch((error) => {
        console.error("Failed to fetch events:", error);
      });
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950 px-8 py-5">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-wide">
              AEGIS ONE
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              AI Cyber Security War Room
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-sm text-emerald-400">
              System Operational
            </span>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="min-h-[calc(100vh-89px)] w-60 border-r border-slate-800 bg-slate-900/50 p-5">
          <nav className="space-y-2">
            <div className="rounded-lg bg-blue-600 px-4 py-3 font-medium">
              Dashboard
            </div>

            <div className="rounded-lg px-4 py-3 text-slate-400 hover:bg-slate-800">
              Incidents
            </div>

            <div className="rounded-lg px-4 py-3 text-slate-400 hover:bg-slate-800">
              Threat Intelligence
            </div>

            <div className="rounded-lg px-4 py-3 text-slate-400 hover:bg-slate-800">
              Attack Graph
            </div>

            <div className="rounded-lg px-4 py-3 text-slate-400 hover:bg-slate-800">
              AI Analyst
            </div>

            <div className="rounded-lg px-4 py-3 text-slate-400 hover:bg-slate-800">
              Analytics
            </div>
          </nav>
        </aside>

        {/* Main Dashboard */}
        <section className="flex-1 p-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold">Security Overview</h2>
            <p className="mt-2 text-slate-400">
              Monitor security events, incidents and AI-assisted
              investigations.
            </p>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <p className="text-sm text-slate-400">Active Incidents</p>
              <p className="mt-3 text-4xl font-bold">12</p>
            </div>

            <div className="rounded-xl border border-red-900/50 bg-slate-900 p-6">
              <p className="text-sm text-slate-400">Critical</p>
              <p className="mt-3 text-4xl font-bold text-red-400">3</p>
            </div>

            <div className="rounded-xl border border-orange-900/50 bg-slate-900 p-6">
              <p className="text-sm text-slate-400">High</p>
              <p className="mt-3 text-4xl font-bold text-orange-400">5</p>
            </div>

            <div className="rounded-xl border border-yellow-900/50 bg-slate-900 p-6">
              <p className="text-sm text-slate-400">Medium</p>
              <p className="mt-3 text-4xl font-bold text-yellow-400">4</p>
            </div>
          </div>

          {/* Recent Incidents */}
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900">
            <div className="border-b border-slate-800 p-6">
              <h3 className="text-xl font-semibold">Recent Incidents</h3>
              <p className="mt-1 text-sm text-slate-400">
                Incidents requiring analyst attention
              </p>
            </div>

            <div className="divide-y divide-slate-800">
              <div className="flex items-center justify-between p-5">
                <div>
                  <p className="font-medium">
                    Possible Account Compromise
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Brute Force → Privilege Activity → Data Access
                  </p>
                </div>

                <span className="rounded-full bg-red-500/10 px-3 py-1 text-sm text-red-400">
                  CRITICAL
                </span>
              </div>

              <div className="flex items-center justify-between p-5">
                <div>
                  <p className="font-medium">
                    Suspicious Network Activity
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Port Scanning detected
                  </p>
                </div>

                <span className="rounded-full bg-orange-500/10 px-3 py-1 text-sm text-orange-400">
                  HIGH
                </span>
              </div>

              <div className="flex items-center justify-between p-5">
                <div>
                  <p className="font-medium">
                    Unusual File Activity
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Isolation Forest anomaly
                  </p>
                </div>

                <span className="rounded-full bg-yellow-500/10 px-3 py-1 text-sm text-yellow-400">
                  MEDIUM
                </span>
              </div>
            </div>
          </div>

          {/* AI Investigation */}
          <div className="mt-8 rounded-xl border border-blue-900/50 bg-slate-900 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold">
                  AI Investigation
                </h3>
                <p className="mt-1 text-sm text-slate-400">
                  Evidence-grounded investigation and recommendations
                </p>
              </div>

              <span className="rounded-full bg-blue-500/10 px-3 py-1 text-sm text-blue-400">
                AI ASSISTED
              </span>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-slate-800 p-4">
                <p className="text-sm text-slate-400">Detection</p>
                <p className="mt-2 font-medium">
                  XGBoost + Anomaly Detection
                </p>
              </div>

              <div className="rounded-lg bg-slate-800 p-4">
                <p className="text-sm text-slate-400">Context</p>
                <p className="mt-2 font-medium">
                  MITRE ATT&CK + RAG
                </p>
              </div>

              <div className="rounded-lg bg-slate-800 p-4">
                <p className="text-sm text-slate-400">Decision</p>
                <p className="mt-2 font-medium">
                  Human Analyst
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
      {/* Live Security Events */}
<div className="mt-8 rounded-xl border border-slate-800 bg-slate-900">
  <div className="border-b border-slate-800 p-6">
    <h3 className="text-xl font-semibold">Live Security Events</h3>
    <p className="mt-1 text-sm text-slate-400">
      Events received from the Aegis One security database
    </p>
  </div>

  <div className="divide-y divide-slate-800">
    {events.length === 0 ? (
      <div className="p-6 text-slate-400">
        No security events found.
      </div>
    ) : (
      events.map((event) => (
        <div
          key={event.id}
          className="flex items-center justify-between p-5"
        >
          <div>
            <p className="font-medium">{event.event_type}</p>

            <p className="mt-1 text-sm text-slate-400">
              {event.source_ip} → {event.destination_ip}
            </p>

            <p className="mt-1 text-sm text-slate-500">
              {event.description}
            </p>
          </div>

          <span
            className={`rounded-full px-3 py-1 text-sm ${
              event.severity === "CRITICAL"
                ? "bg-red-500/10 text-red-400"
                : event.severity === "HIGH"
                ? "bg-orange-500/10 text-orange-400"
                : "bg-yellow-500/10 text-yellow-400"
            }`}
          >
            {event.severity}
          </span>
        </div>
      ))
    )}
  </div>
</div>
    </main>
  );
}