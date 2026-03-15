import { useState } from 'react';
import type { UpsetAlert } from '../types';

interface Props {
  alerts: UpsetAlert[];
}

function confidenceColor(c: number): string {
  if (c >= 0.7) return 'var(--accent-green)';
  if (c >= 0.5) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

export function UpsetAlerts({ alerts }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (alerts.length === 0) return null;

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border-default)',
      borderRadius: '12px',
      overflow: 'hidden',
    }}>
      <button
        onClick={() => { setExpanded(!expanded); }}
        style={{
          width: '100%',
          padding: '12px 20px',
          background: 'none',
          border: 'none',
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.9rem',
        }}
      >
        <span>
          <span style={{ color: 'var(--accent-orange)', marginRight: '8px' }}>&#9888;</span>
          Upset Alerts ({String(alerts.length)})
        </span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          {expanded ? '▲ Collapse' : '▼ Expand'}
        </span>
      </button>

      {expanded && (
        <div style={{ padding: '0 20px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {alerts.map((alert) => (
            <div
              key={alert.matchup}
              style={{
                background: 'var(--bg-primary)',
                borderLeft: '3px solid var(--accent-orange)',
                borderRadius: '6px',
                padding: '10px 14px',
                display: 'flex',
                gap: '16px',
                alignItems: 'flex-start',
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                  {alert.matchup}
                  <span style={{
                    marginLeft: '8px',
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    textTransform: 'capitalize',
                  }}>
                    ({alert.region})
                  </span>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                  {alert.reasons.map((r) => (
                    <span
                      key={r}
                      style={{
                        fontSize: '0.7rem',
                        background: 'var(--bg-tertiary)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {r}
                    </span>
                  ))}
                </div>
              </div>
              <div style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: confidenceColor(alert.confidence),
                whiteSpace: 'nowrap',
              }}>
                {(alert.confidence * 100).toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
