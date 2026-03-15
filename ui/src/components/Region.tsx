import type { Matchup as MatchupType, TeamMetrics } from '../types';
import { Matchup } from './Matchup';
import { matchupId } from '../lib/cascade';

interface Props {
  regionName: string;
  rounds: Record<string, MatchupType[]>;
  overrides: Map<string, string>;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
  flip?: boolean; // If true, render right-to-left (for right-side regions)
}

const ROUND_KEYS = ['r64', 'r32', 'sweet_16', 'elite_8'] as const;
const ROUND_LABELS: Record<string, string> = {
  r64: 'R64',
  r32: 'R32',
  sweet_16: 'S16',
  elite_8: 'E8',
};

export function Region({ regionName, rounds, overrides, teamData, onOverride, flip }: Props) {
  const orderedKeys = flip ? [...ROUND_KEYS].reverse() : [...ROUND_KEYS];

  return (
    <div>
      <div style={{
        textTransform: 'capitalize',
        fontWeight: 700,
        fontSize: '1rem',
        color: 'var(--accent-purple)',
        marginBottom: '8px',
        textAlign: flip ? 'right' : 'left',
        padding: '0 4px',
      }}>
        {regionName}
      </div>
      <div style={{
        display: 'flex',
        gap: '4px',
        alignItems: 'stretch',
      }}>
        {orderedKeys.map((roundKey) => {
          const matchups = rounds[roundKey] ?? [];
          // Calculate spacing for vertical centering
          // R64=8, R32=4, S16=2, E8=1
          const roundIdx = ROUND_KEYS.indexOf(roundKey);
          const verticalGap = roundIdx === 0 ? 4 : (Math.pow(2, roundIdx) * 4 + (Math.pow(2, roundIdx) - 1) * 52);

          return (
            <div
              key={roundKey}
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-around',
                gap: `${String(verticalGap)}px`,
                minWidth: '164px',
              }}
            >
              <div style={{
                fontSize: '0.6rem',
                color: 'var(--text-muted)',
                textAlign: 'center',
                marginBottom: '2px',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
              }}>
                {ROUND_LABELS[roundKey] ?? roundKey}
              </div>
              {matchups.map((m, idx) => {
                const mId = matchupId(regionName, roundKey, idx);
                return (
                  <Matchup
                    key={mId}
                    matchup={m}
                    matchupId={mId}
                    isOverridden={overrides.has(mId)}
                    teamData={teamData}
                    onOverride={onOverride}
                  />
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
