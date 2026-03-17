import type { Matchup as MatchupType, TeamMetrics } from '../types';
import { Matchup } from './Matchup';
import { matchupId } from '../lib/cascade';

interface Props {
  regionName: string;
  rounds: Record<string, MatchupType[]>;
  overrides: Map<string, string>;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
  onShowMatchupDetails?: (matchup: MatchupType) => void;
  flip?: boolean;
}

const ROUND_KEYS = ['r64', 'r32', 'sweet_16', 'elite_8'] as const;
const ROUND_LABELS: Record<string, string> = {
  r64: 'R64',
  r32: 'R32',
  sweet_16: 'S16',
  elite_8: 'E8',
};

// Matchup card height (approx) — two team rows + divider + padding
const MATCHUP_H = 56;
const MATCHUP_GAP = 8;

export function Region({ regionName, rounds, overrides, teamData, onOverride, onShowMatchupDetails, flip }: Props) {
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

      {/* Round headers */}
      <div style={{ display: 'flex', gap: '24px', marginBottom: '4px' }}>
        {orderedKeys.map((rk) => (
          <div key={rk} style={{
            width: '182px',
            fontSize: '0.6rem',
            color: 'var(--text-muted)',
            textAlign: 'center',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}>
            {ROUND_LABELS[rk] ?? rk}
          </div>
        ))}
      </div>

      {/* Bracket grid — use relative positioning for proper alignment */}
      <div style={{ display: 'flex', gap: '24px', position: 'relative' }}>
        {orderedKeys.map((roundKey) => {
          const matchups = rounds[roundKey] ?? [];
          const roundIdx = ROUND_KEYS.indexOf(roundKey);

          // For each round, the matchup should be vertically centered
          // between its two feeder matchups from the previous round.
          // R64: 8 matchups, evenly spaced
          // R32: 4 matchups, each centered between pairs of R64
          // S16: 2 matchups, each centered between pairs of R32
          // E8: 1 matchup, centered between the two S16

          // Height of one "slot" in R64 (matchup + gap)
          const slotH = MATCHUP_H + MATCHUP_GAP;

          // For round N, each matchup spans 2^N R64 slots
          const slotsPerMatchup = Math.pow(2, roundIdx);

          // Total height of the R64 column
          const totalHeight = 8 * slotH - MATCHUP_GAP;

          return (
            <div
              key={roundKey}
              style={{
                position: 'relative',
                width: '182px',
                height: `${totalHeight}px`,
              }}
            >
              {matchups.map((m, idx) => {
                const mId = matchupId(regionName, roundKey, idx);

                // Center of the block this matchup occupies
                const blockStart = idx * slotsPerMatchup * slotH;
                const blockEnd = blockStart + slotsPerMatchup * slotH - MATCHUP_GAP;
                const centerY = (blockStart + blockEnd) / 2;
                const top = centerY - MATCHUP_H / 2;

                return (
                  <div
                    key={mId}
                    style={{
                      position: 'absolute',
                      top: `${top}px`,
                      left: 0,
                      right: 0,
                    }}
                  >
                    <Matchup
                      matchup={m}
                      matchupId={mId}
                      isOverridden={overrides.has(mId)}
                      teamData={teamData}
                      onOverride={onOverride}
                      onShowDetails={onShowMatchupDetails}
                    />
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
