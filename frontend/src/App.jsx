import React, { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setData(null);
    try {
      const res = await fetch(`/api/profile?q=${query}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div style={{ fontFamily: "Arial", textAlign: "center", marginTop: "60px" }}>
      <h1>Profiler.AI OSINT Demo</h1>
      <input
        type="text"
        placeholder="Enter username, email, or phone"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{
          padding: "10px",
          width: "300px",
          marginRight: "10px",
          borderRadius: "6px",
        }}
      />
      <button
        onClick={handleSearch}
        style={{
          padding: "10px 20px",
          borderRadius: "6px",
          background: "#007bff",
          color: "white",
          border: "none",
          cursor: "pointer",
        }}
      >
        Search
      </button>

      {loading && <p>Fetching data...</p>}

      {data && (
        <div style={{ marginTop: "40px", textAlign: "left", display: "inline-block" }}>
          <h3>Extracted Entities:</h3>
          <pre
            style={{
              background: "#f4f4f4",
              padding: "10px",
              borderRadius: "5px",
              width: "500px",
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
