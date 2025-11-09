import React, { useState } from "react";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, ArcElement, Tooltip, Legend);

const styles = {
  container: { fontFamily: "Inter, Arial, sans-serif", padding: 20, maxWidth: 1100, margin: "0 auto" },
  header: { display: "flex", alignItems: "center", gap: 12 },
  input: { padding: 10, width: 420, borderRadius: 6, border: "1px solid #ddd" },
  btn: { padding: "10px 14px", borderRadius: 6, background: "#1f77b4", color: "#fff", border: "none", cursor: "pointer" },
  layout: { display: "grid", gridTemplateColumns: "1fr 420px", gap: 20, marginTop: 20 },
  panel: { background: "#fff", padding: 14, borderRadius: 8, boxShadow: "0 6px 18px rgba(15,15,15,0.06)" },
  pre: { whiteSpace: "pre-wrap", maxHeight: 360, overflowY: "auto", fontSize: 13, lineHeight: 1.4 },
  cardsGrid: { display: "grid", gridTemplateColumns: "repeat(1, 1fr)", gap: 12, marginTop: 12 },
  actorCard: { borderLeft: "4px solid #ff7f0e", padding: 12, borderRadius: 6, background: "#fff" },
  small: { fontSize: 12, color: "#666" }
};

function ActorCard({ a }) {
  return (
    <div style={styles.actorCard}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <div style={{ fontWeight: 700 }}>{a.username || a.email || "unknown"}</div>
          <div style={styles.small}>{a.platform} • {a.country || "—"}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{a.risk_level || "Medium"}</div>
          <div style={styles.small}>conf {Math.round((a.confidence || a.confidence === 0 ? a.confidence : (a.conf || 0)) * 100) / 100}</div>
        </div>
      </div>
      <div style={{ marginTop: 8, color: "#333" }}>{a.note || a.activity_type || "No extra context."}</div>
    </div>
  );
}

export default function App() {
  const [q, setQ] = useState("");
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runQuery() {
    if (!q) return;
    setLoading(true);
    setProfile(null);
    try {
      const res = await fetch(`/api/profile?q=${encodeURIComponent(q)}`);
      const js = await res.json();
      setProfile(js);
    } catch (err) {
      console.error(err);
      alert("Error fetching profile. Check backend.");
    }
    setLoading(false);
  }

  // Chart data builders
  function buildRiskBar(actor_intel = []) {
    const buckets = { Critical: 0, High: 0, Medium: 0, Low: 0 };
    actor_intel.forEach(a => {
      const r = (a.risk_level || a.risk || "Medium");
      if (buckets[r] !== undefined) buckets[r] += 1;
      else buckets.Medium += 1;
    });
    return {
      labels: Object.keys(buckets),
      datasets: [{ label: "Actors", data: Object.values(buckets), backgroundColor: ["#8b0000","#ff5733","#f4b400","#2ca02c"] }]
    };
  }

  function buildBreachYears(breach_data = []) {
    const counts = {};
    (breach_data || []).forEach(b => {
      const y = b.Year || b.year || (b.get && b.get('Year')) || "Unknown";
      const num = typeof y === "number" ? y : parseInt(y) || "Unknown";
      counts[num] = (counts[num] || 0) + 1;
    });
    const labels = Object.keys(counts).sort((a,b)=> (a==="Unknown"?1:0) - (b==="Unknown"?1:0) || a - b);
    const data = labels.map(l => counts[l]);
    return { labels, datasets: [{ label: "Breaches", data, backgroundColor: "#1f77b4" }] };
  }

  function buildThreatGauge(profile) {
    const value = (profile && profile.scores && profile.scores.final_threat_score) || 0;
    return {
      labels: ["Risk", "Remaining"],
      datasets: [{
        data: [value, Math.max(0, 100 - value)],
        backgroundColor: ["#d62728", "#e9e9e9"],
        hoverOffset: 4
      }]
    };
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={{ margin: 0 }}>Profiler.AI — Visual Dashboard</h1>
      </div>

      <div style={{ marginTop: 12 }}>
        <input style={styles.input} value={q} onChange={e=>setQ(e.target.value)} placeholder="Enter email / username / phone" />
        <button style={styles.btn} onClick={runQuery} disabled={loading} >{loading ? "Running..." : "Run"}</button>
      </div>

      {profile && (
        <div style={styles.layout}>
          {/* Left: descriptive + actor cards + charts */}
          <div>
            <div style={styles.panel}>
              <h3 style={{ marginTop: 0 }}>Descriptive Report</h3>
              <div style={styles.pre}>{profile.descriptive_report || profile.summary || "No narrative available."}</div>
              <div style={{ marginTop: 8 }}>
                <button style={{ ...styles.btn, background: "#2c7be5" }} onClick={()=>{
                  // copy to clipboard
                  navigator.clipboard.writeText(profile.descriptive_report || profile.summary || "");
                  alert("Copied descriptive report to clipboard.");
                }}>Copy Report</button>
              </div>
            </div>

            <div style={{ marginTop: 12, ...styles.panel }}>
              <h3 style={{ marginTop: 0 }}>Actor Intelligence</h3>
              <div style={styles.cardsGrid}>
                {(profile.actor_intel && profile.actor_intel.length) ? (
                  profile.actor_intel.slice(0,8).map((a,i)=><ActorCard key={i} a={a} />)
                ) : <div style={styles.small}>No actor intelligence signals detected.</div>}
              </div>
            </div>
          </div>

          {/* Right: charts & summary */}
          <div>
            <div style={styles.panel}>
              <h3 style={{ marginTop: 0 }}>Threat Overview</h3>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <div style={{ width: 220 }}>
                  <Doughnut data={buildThreatGauge(profile)} />
                </div>
                <div>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{(profile.scores && profile.scores.final_threat_score) || 0}/100</div>
                  <div style={styles.small}>Breach impact: {(profile.scores && profile.scores.breach_impact_score) || 0}</div>
                  <div style={styles.small}>Actor boost: {(profile.scores && profile.scores.actor_boost_estimate) || 0}</div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: 12, ...styles.panel }}>
              <h3 style={{ marginTop: 0 }}>Risk-level Distribution</h3>
              <Bar data={buildRiskBar(profile.actor_intel || [])} options={{ responsive: true, plugins: { legend: { display: false }}}} />
            </div>

            <div style={{ marginTop: 12, ...styles.panel }}>
              <h3 style={{ marginTop: 0 }}>Breach Year Histogram</h3>
              <Bar data={buildBreachYears(profile.breach_data || [])} options={{ responsive: true, plugins: { legend: { display: false }}}} />
            </div>

            <div style={{ marginTop: 12, ...styles.panel }}>
              <h3 style={{ marginTop: 0 }}>Raw JSON / Details</h3>
              <pre style={{ maxHeight: 220, overflowY: "auto" }}>{JSON.stringify(profile, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}

      {!profile && <div style={{ marginTop: 16, color: "#666" }}>Enter a query and press Run. Sample queries: <b>zomato</b>, <b>rohan</b>, <b>alice@gmail.com</b></div>}
    </div>
  );
}
