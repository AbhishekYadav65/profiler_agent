import React, {useState} from 'react'

function Node({x,y,label}){
  return (
    <g transform={`translate(${x},${y})`}>
      <circle r={28} fill="#1f77b4"></circle>
      <text x={0} y={4} textAnchor="middle" fill="#fff" style={{fontSize:10}}>{label}</text>
    </g>
  )
}

export default function App(){
  const [q,setQ] = useState('')
  const [profile,setProfile] = useState(null)
  const [loading,setLoading] = useState(false)

  async function run(){
    if(!q) return
    setLoading(true)
    const res = await fetch(`/api/profile?q=${encodeURIComponent(q)}`)
    const js = await res.json()
    setProfile(js)
    setLoading(false)
  }

  return (
    <div style={{fontFamily:'Arial, sans-serif', padding:20}}>
      <h2>Profiler.AI — Prototype</h2>
      <div style={{marginBottom:12}}>
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Enter email / username / phone" style={{padding:8,width:420}} />
        <button onClick={run} style={{marginLeft:8,padding:'8px 12px'}}>Run</button>
      </div>

      {loading && <div>Running profile...</div>}

      {profile && (
        <div>
          <h3>Summary</h3>
          <div style={{background:'#f4f4f4', padding:10}}>{profile.summary || 'No summary'}</div>

          <h3>Clusters (entities)</h3>
          <ul>
            {profile.clusters.map((c,idx)=> (
              <li key={idx}>{c.type} — <b>{c.value}</b> (score: {c.score}) — occurrences: {c.occurrences.length}</li>
            ))}
          </ul>

          <h3>Graph</h3>
          <svg width={700} height={320} style={{border:'1px solid #ddd'}}>
            {/* simple radial layout */}
            {profile.clusters.map((c,i)=>{
              const angle = (i / Math.max(1, profile.clusters.length)) * Math.PI * 2
              const cx = 350 + Math.cos(angle) * 140
              const cy = 160 + Math.sin(angle) * 90
              return <Node key={i} x={cx} y={cy} label={`${c.type}:${c.value.substring(0,12)}`} />
            })}
            {/* center node */}
            <g transform="translate(350,160)">
              <circle r={36} fill="#ff7f0e" />
              <text x={0} y={4} textAnchor="middle" fill="#fff">{profile.query}</text>
            </g>
          </svg>

          <div style={{marginTop:12}}>
            <button onClick={async ()=>{
              const r = await fetch('/api/report', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(profile)})
              const js = await r.json()
              alert('Report generated: ' + JSON.stringify(js))
            }}>Generate Report (PDF + hash)</button>
          </div>
        </div>
      )}
    </div>
  )
}
