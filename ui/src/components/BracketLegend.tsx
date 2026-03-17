export function BracketLegend() {
  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '16px',
      padding: '10px 16px',
      background: 'rgba(30, 33, 48, 0.5)',
      borderRadius: '8px',
      marginBottom: '12px',
      alignItems: 'center',
    }}>
      <span style={{
        fontSize: '0.7rem',
        fontWeight: 700,
        color: '#94a3b8',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      }}>
        Key
      </span>

      {/* Winner */}
      <LegendItem
        swatch={<div style={{
          width: '28px', height: '14px', borderRadius: '3px',
          background: 'rgba(74, 222, 128, 0.12)',
          borderLeft: '3px solid #4ade80',
        }} />}
        label="Winner"
      />

      {/* Toss-up */}
      <LegendItem
        swatch={<div style={{
          width: '28px', height: '18px', borderRadius: '4px',
          border: '2px solid #f1c40f',
          borderLeftWidth: '4px',
          background: 'rgba(241, 196, 15, 0.06)',
        }} />}
        label="Toss-up (< 60%)"
      />

      {/* Upset pick */}
      <LegendItem
        swatch={<div style={{
          width: '28px', height: '18px', borderRadius: '4px',
          border: '2px solid #e84393',
          borderLeftWidth: '4px',
        }} />}
        label="Upset pick"
      />

      {/* Locked */}
      <LegendItem
        swatch={<div style={{
          width: '28px', height: '18px', borderRadius: '4px',
          border: '2px solid #2d3348',
          background: 'rgba(30, 33, 48, 0.5)',
          opacity: 0.7,
        }} />}
        label="Locked (> 90%)"
      />

      {/* Override */}
      <LegendItem
        swatch={<div style={{
          width: '28px', height: '18px', borderRadius: '4px',
          border: '2px dashed #94a3b8',
        }} />}
        label="Your override"
      />

      <span style={{ color: '#2d3348', margin: '0 4px' }}>|</span>

      {/* Prob colors */}
      <LegendItem
        swatch={<span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#4ade80' }}>72%</span>}
        label="Strong"
      />
      <LegendItem
        swatch={<span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#facc15' }}>55%</span>}
        label="Close"
      />
      <LegendItem
        swatch={<span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#f87171' }}>38%</span>}
        label="Underdog"
      />

      <span style={{ color: '#2d3348', margin: '0 4px' }}>|</span>

      <span style={{ fontSize: '0.65rem', color: '#64748b' }}>
        Click losing team to override &middot; Click <span style={{ fontSize: '0.85rem', verticalAlign: 'middle' }}>&#x2139;</span> for details
      </span>
    </div>
  );
}

function LegendItem({ swatch, label }: { swatch: React.ReactNode; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      {swatch}
      <span style={{ fontSize: '0.7rem', color: '#cbd5e1' }}>{label}</span>
    </div>
  );
}
