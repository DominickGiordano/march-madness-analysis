import { Modal } from './Modal';
import type { Matchup, TeamMetrics } from '../types';

interface Props {
  matchup: Matchup;
  teamData: Record<string, TeamMetrics>;
  onClose: () => void;
}

const ROUND_NAMES: Record<number, string> = {
  1: 'Round of 64',
  2: 'Round of 32',
  3: 'Sweet 16',
  4: 'Elite 8',
  5: 'Final Four',
  6: 'Championship',
};

interface MetricDef {
  label: string;
  key: string;
  format: (v: number) => string;
  higherBetter: boolean;
}

const METRICS: MetricDef[] = [
  { label: 'Seed', key: 'seed', format: (v) => `#${String(v)}`, higherBetter: false },
  { label: 'Barthag', key: 'barthag', format: (v) => v.toFixed(4), higherBetter: true },
  { label: 'AdjO', key: 'adj_o', format: (v) => v.toFixed(1), higherBetter: true },
  { label: 'AdjO Rank', key: 'adj_o_rank', format: (v) => `#${String(v)}`, higherBetter: false },
  { label: 'AdjD', key: 'adj_d', format: (v) => v.toFixed(1), higherBetter: false },
  { label: 'AdjD Rank', key: 'adj_d_rank', format: (v) => `#${String(v)}`, higherBetter: false },
  { label: 'Win %', key: 'win_pct', format: (v) => `${(v * 100).toFixed(1)}%`, higherBetter: true },
  { label: 'WAB', key: 'wab', format: (v) => v.toFixed(1), higherBetter: true },
  { label: 'Tempo', key: 'tempo', format: (v) => v.toFixed(1), higherBetter: true },
  { label: 'Momentum', key: 'momentum', format: (v) => v.toFixed(4), higherBetter: true },
  { label: 'eFG Ratio', key: 'efg_ratio', format: (v) => v.toFixed(3), higherBetter: true },
  { label: 'SOS', key: 'sos_proxy', format: (v) => v.toFixed(4), higherBetter: true },
];

function getMetricValue(team: TeamMetrics, key: string): number | undefined {
  return (team as unknown as Record<string, number>)[key] as number | undefined;
}

function isBetter(a: number, b: number, higherBetter: boolean): boolean {
  return higherBetter ? a > b : a < b;
}

export function MatchupModal({ matchup, teamData, onClose }: Props) {
  const teamA = teamData[matchup.teamA];
  const teamB = teamData[matchup.teamB];
  const roundName = ROUND_NAMES[matchup.round] ?? `Round ${String(matchup.round)}`;
  const seedA = teamA?.seed;
  const seedB = teamB?.seed;

  const title = `${roundName}: #${String(seedA ?? '?')} ${matchup.teamA} vs #${String(seedB ?? '?')} ${matchup.teamB}`;

  const probA = matchup.winner === matchup.teamA ? matchup.winProb : 1 - matchup.winProb;
  const probB = 1 - probA;
  const pctA = Math.round(probA * 100);
  const pctB = Math.round(probB * 100);

  return (
    <Modal title={title} onClose={onClose}>
      {/* Win probability bar */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          fontWeight: 600,
          marginBottom: '6px',
        }}>
          <span style={{ color: probA >= probB ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
            {matchup.teamA} {String(pctA)}%
          </span>
          <span style={{ color: probB >= probA ? 'var(--accent-green)' : 'var(--text-secondary)' }}>
            {String(pctB)}% {matchup.teamB}
          </span>
        </div>
        <div style={{
          display: 'flex',
          height: '10px',
          borderRadius: '5px',
          overflow: 'hidden',
          background: 'var(--bg-tertiary)',
        }}>
          <div style={{
            width: `${String(pctA)}%`,
            background: probA >= probB
              ? 'linear-gradient(90deg, var(--accent-blue), var(--accent-green))'
              : 'var(--text-muted)',
            transition: 'width 0.3s ease',
          }} />
          <div style={{
            width: `${String(pctB)}%`,
            background: probB > probA
              ? 'linear-gradient(90deg, var(--accent-green), var(--accent-blue))'
              : 'var(--text-muted)',
            transition: 'width 0.3s ease',
          }} />
        </div>
      </div>

      {/* Side-by-side metrics */}
      {teamA && teamB && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '0',
          fontSize: '0.8rem',
        }}>
          {/* Header row */}
          <div style={{ fontWeight: 700, textAlign: 'center', padding: '6px 8px', color: 'var(--accent-blue)' }}>
            {matchup.teamA}
          </div>
          <div style={{ fontWeight: 600, textAlign: 'center', padding: '6px 12px', color: 'var(--text-muted)' }}>
            Metric
          </div>
          <div style={{ fontWeight: 700, textAlign: 'center', padding: '6px 8px', color: 'var(--accent-blue)' }}>
            {matchup.teamB}
          </div>

          {METRICS.map((metric) => {
            const valA = getMetricValue(teamA, metric.key);
            const valB = getMetricValue(teamB, metric.key);
            const aWins = valA !== undefined && valB !== undefined && isBetter(valA, valB, metric.higherBetter);
            const bWins = valA !== undefined && valB !== undefined && isBetter(valB, valA, metric.higherBetter);

            return (
              <div key={metric.key} style={{ display: 'contents' }}>
                <div style={{
                  textAlign: 'center',
                  padding: '5px 8px',
                  color: aWins ? 'var(--accent-green)' : 'var(--text-secondary)',
                  fontWeight: aWins ? 600 : 400,
                  background: aWins ? 'rgba(34, 197, 94, 0.08)' : 'transparent',
                  borderRadius: '4px',
                }}>
                  {valA !== undefined ? metric.format(valA) : '---'}
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
                  color: bWins ? 'var(--accent-green)' : 'var(--text-secondary)',
                  fontWeight: bWins ? 600 : 400,
                  background: bWins ? 'rgba(34, 197, 94, 0.08)' : 'transparent',
                  borderRadius: '4px',
                }}>
                  {valB !== undefined ? metric.format(valB) : '---'}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Injury info */}
      {(teamA?.injury_adjusted || teamB?.injury_adjusted) && (
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
          {teamA?.injury_adjusted && teamA.barthag_original !== undefined && (
            <div style={{ color: 'var(--text-secondary)', marginBottom: '2px' }}>
              {matchup.teamA}: Barthag adjusted from {teamA.barthag_original.toFixed(4)} to {teamA.barthag.toFixed(4)} ({((teamA.barthag - teamA.barthag_original) * 100).toFixed(2)}%)
            </div>
          )}
          {teamB?.injury_adjusted && teamB.barthag_original !== undefined && (
            <div style={{ color: 'var(--text-secondary)' }}>
              {matchup.teamB}: Barthag adjusted from {teamB.barthag_original.toFixed(4)} to {teamB.barthag.toFixed(4)} ({((teamB.barthag - teamB.barthag_original) * 100).toFixed(2)}%)
            </div>
          )}
        </div>
      )}

      {/* Matchup flags */}
      <div style={{
        marginTop: '12px',
        display: 'flex',
        gap: '8px',
        flexWrap: 'wrap',
      }}>
        {matchup.isUpset && (
          <span style={{
            padding: '3px 10px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: 'rgba(249, 115, 22, 0.15)',
            color: 'var(--accent-orange)',
          }}>
            Upset Pick
          </span>
        )}
        {matchup.locked && (
          <span style={{
            padding: '3px 10px',
            borderRadius: '4px',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: 'rgba(107, 114, 128, 0.15)',
            color: 'var(--text-muted)',
          }}>
            Locked ({">"} 90% probability)
          </span>
        )}
      </div>
    </Modal>
  );
}
