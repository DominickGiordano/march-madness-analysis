import { Modal } from './Modal';
import type { UpsetAlert, TeamMetrics } from '../types';

interface Props {
  alert: UpsetAlert;
  teamData: Record<string, TeamMetrics>;
  onClose: () => void;
}

const SEED_UPSET_RATES: Record<string, string> = {
  '1v16': '1%',
  '2v15': '6%',
  '3v14': '15%',
  '4v13': '21%',
  '5v12': '35%',
  '6v11': '37%',
  '7v10': '39%',
  '8v9': '50%',
};

function getHistoricalRate(higher: number, lower: number): string {
  const key = `${String(higher)}v${String(lower)}`;
  return SEED_UPSET_RATES[key] ?? '---';
}

function confidenceColor(c: number): string {
  if (c >= 0.7) return 'var(--accent-green)';
  if (c >= 0.5) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

export function UpsetModal({ alert, teamData, onClose }: Props) {
  const favorite = teamData[alert.higherTeam];
  const underdog = teamData[alert.lowerTeam];
  const title = `${alert.matchup} (${alert.region.charAt(0).toUpperCase() + alert.region.slice(1)})`;
  const historicalRate = getHistoricalRate(alert.higherSeed, alert.lowerSeed);
  const pct = Math.round(alert.confidence * 100);

  return (
    <Modal title={title} onClose={onClose}>
      {/* Confidence meter */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '6px',
        }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Upset Confidence</span>
          <span style={{
            fontSize: '1rem',
            fontWeight: 700,
            color: confidenceColor(alert.confidence),
          }}>
            {String(pct)}%
          </span>
        </div>
        <div style={{
          height: '8px',
          borderRadius: '4px',
          background: 'var(--bg-tertiary)',
          overflow: 'hidden',
        }}>
          <div style={{
            width: `${String(pct)}%`,
            height: '100%',
            borderRadius: '4px',
            background: `linear-gradient(90deg, var(--accent-orange), ${confidenceColor(alert.confidence)})`,
            transition: 'width 0.3s ease',
          }} />
        </div>
      </div>

      {/* Reasons */}
      <div style={{
        marginBottom: '20px',
        padding: '12px 16px',
        background: 'var(--bg-tertiary)',
        borderRadius: '8px',
        borderLeft: '3px solid var(--accent-orange)',
      }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-orange)', marginBottom: '8px' }}>
          Why This Upset?
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {alert.reasons.map((reason) => (
            <li key={reason} style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              paddingLeft: '14px',
              position: 'relative',
            }}>
              <span style={{ position: 'absolute', left: 0, color: 'var(--accent-orange)' }}>&#x2022;</span>
              {reason}
            </li>
          ))}
        </ul>
      </div>

      {/* Historical context */}
      <div style={{
        marginBottom: '20px',
        padding: '10px 14px',
        background: 'rgba(139, 92, 246, 0.08)',
        border: '1px solid rgba(139, 92, 246, 0.2)',
        borderRadius: '8px',
        fontSize: '0.8rem',
        color: 'var(--text-secondary)',
      }}>
        <span style={{ fontWeight: 600, color: 'var(--accent-purple)' }}>Historical context: </span>
        #{String(alert.higherSeed)} vs #{String(alert.lowerSeed)} seeds have a {historicalRate} upset rate historically
      </div>

      {/* Side-by-side comparison */}
      {favorite && underdog && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '0',
          fontSize: '0.8rem',
        }}>
          {/* Header */}
          <div style={{
            fontWeight: 700,
            textAlign: 'center',
            padding: '6px 8px',
            color: 'var(--text-secondary)',
          }}>
            #{String(alert.higherSeed)} {alert.higherTeam}
            <div style={{ fontSize: '0.65rem', fontWeight: 400, color: 'var(--text-muted)' }}>Favored</div>
          </div>
          <div style={{ fontWeight: 600, textAlign: 'center', padding: '6px 12px', color: 'var(--text-muted)' }}>
            vs
          </div>
          <div style={{
            fontWeight: 700,
            textAlign: 'center',
            padding: '6px 8px',
            color: 'var(--accent-orange)',
          }}>
            #{String(alert.lowerSeed)} {alert.lowerTeam}
            <div style={{ fontSize: '0.65rem', fontWeight: 400, color: 'var(--text-muted)' }}>Underdog</div>
          </div>

          {/* Metrics */}
          {([
            { label: 'Barthag', key: 'barthag' as const, format: (v: number) => v.toFixed(4), higherBetter: true },
            { label: 'AdjD', key: 'adj_d' as const, format: (v: number) => v.toFixed(1), higherBetter: false },
            { label: 'AdjD Rank', key: 'adj_d_rank' as const, format: (v: number) => `#${String(v)}`, higherBetter: false },
            { label: 'AdjO', key: 'adj_o' as const, format: (v: number) => v.toFixed(1), higherBetter: true },
            { label: 'Win %', key: 'win_pct' as const, format: (v: number) => `${(v * 100).toFixed(1)}%`, higherBetter: true },
            { label: 'WAB', key: 'wab' as const, format: (v: number) => v.toFixed(1), higherBetter: true },
            { label: 'Momentum', key: 'momentum' as const, format: (v: number) => v.toFixed(4), higherBetter: true },
            { label: 'eFG Ratio', key: 'efg_ratio' as const, format: (v: number) => v.toFixed(3), higherBetter: true },
          ] as const).map((metric) => {
            const valFav = favorite[metric.key];
            const valUnd = underdog[metric.key];
            const favWins = metric.higherBetter ? valFav > valUnd : valFav < valUnd;
            const undWins = !favWins && valFav !== valUnd;

            return (
              <div key={metric.key} style={{ display: 'contents' }}>
                <div style={{
                  textAlign: 'center',
                  padding: '5px 8px',
                  color: favWins ? 'var(--accent-green)' : 'var(--text-secondary)',
                  fontWeight: favWins ? 600 : 400,
                  background: favWins ? 'rgba(34, 197, 94, 0.08)' : 'transparent',
                  borderRadius: '4px',
                }}>
                  {metric.format(valFav)}
                </div>
                <div style={{
                  textAlign: 'center',
                  padding: '5px 12px',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  borderLeft: '1px solid var(--border-default)',
                  borderRight: '1px solid var(--border-default)',
                }}>
                  {metric.label}
                </div>
                <div style={{
                  textAlign: 'center',
                  padding: '5px 8px',
                  color: undWins ? 'var(--accent-green)' : 'var(--text-secondary)',
                  fontWeight: undWins ? 600 : 400,
                  background: undWins ? 'rgba(34, 197, 94, 0.08)' : 'transparent',
                  borderRadius: '4px',
                }}>
                  {metric.format(valUnd)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Injury info */}
      {(favorite?.injury_adjusted || underdog?.injury_adjusted) && (
        <div style={{
          marginTop: '16px',
          padding: '10px 14px',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '8px',
          fontSize: '0.8rem',
        }}>
          <div style={{ fontWeight: 600, color: 'var(--accent-red)', marginBottom: '4px' }}>
            Injury Adjustments
          </div>
          {favorite?.injury_adjusted && favorite.barthag_original !== undefined && (
            <div style={{ color: 'var(--text-secondary)', marginBottom: '2px' }}>
              {alert.higherTeam}: Barthag {favorite.barthag_original.toFixed(4)} &#x2192; {favorite.barthag.toFixed(4)}
            </div>
          )}
          {underdog?.injury_adjusted && underdog.barthag_original !== undefined && (
            <div style={{ color: 'var(--text-secondary)' }}>
              {alert.lowerTeam}: Barthag {underdog.barthag_original.toFixed(4)} &#x2192; {underdog.barthag.toFixed(4)}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
