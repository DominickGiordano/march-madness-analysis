import type { Matchup as MatchupType, TeamMetrics } from '../types';

interface Props {
  matchup: MatchupType;
  matchupId: string;
  isOverridden: boolean;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
  onShowDetails?: (matchup: MatchupType) => void;
}

function seedColor(seed: number): string {
  if (seed <= 4) return 'var(--seed-blue)';
  if (seed <= 8) return 'var(--seed-grey)';
  if (seed <= 12) return 'var(--seed-orange)';
  return 'var(--seed-red)';
}

function probColor(prob: number): string {
  if (prob >= 0.7) return '#4ade80';   // bright green
  if (prob >= 0.5) return '#facc15';   // yellow
  return '#f87171';                     // red
}

function TeamRow({
  team,
  seed,
  isWinner,
  isLocked,
  winPct,
  opponent,
  onClick,
}: {
  team: string;
  seed: number | undefined;
  isWinner: boolean;
  isLocked: boolean;
  winPct: number;
  opponent: string;
  onClick: () => void;
}) {
  return (
    <div
      onClick={(e) => {
        if (!isLocked && !isWinner) {
          e.stopPropagation();
          onClick();
        }
      }}
      title={`${team} has ${(winPct * 100).toFixed(0)}% chance to beat ${opponent}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 6px',
        borderRadius: '4px',
        borderLeft: isWinner ? '3px solid #4ade80' : '3px solid transparent',
        background: isWinner ? 'rgba(74, 222, 128, 0.12)' : 'transparent',
        cursor: isLocked || isWinner ? 'default' : 'pointer',
        transition: 'background 0.1s',
      }}
      onMouseEnter={(e) => {
        if (!isLocked && !isWinner) {
          e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isLocked && !isWinner) {
          e.currentTarget.style.background = 'transparent';
        }
      }}
    >
      {seed !== undefined && (
        <span style={{
          fontSize: '0.65rem',
          fontWeight: 700,
          color: '#fff',
          background: seedColor(seed),
          borderRadius: '3px',
          padding: '0 4px',
          minWidth: '18px',
          textAlign: 'center',
          lineHeight: '16px',
        }}>
          {String(seed)}
        </span>
      )}
      <span style={{
        fontSize: '0.75rem',
        fontWeight: isWinner ? 700 : 400,
        color: isWinner ? '#e2e8f0' : '#94a3b8',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        flex: 1,
        maxWidth: '85px',
      }}>
        {team}
      </span>
      {isLocked && (
        <span style={{ fontSize: '0.55rem', opacity: 0.5 }} title="Locked — too lopsided to override">&#128274;</span>
      )}
      <span style={{
        fontSize: '0.6rem',
        fontWeight: 600,
        color: probColor(winPct),
        marginLeft: 'auto',
        flexShrink: 0,
      }}>
        {(winPct * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export function Matchup({ matchup, matchupId: mId, isOverridden, teamData, onOverride, onShowDetails }: Props) {
  const seedA = teamData[matchup.teamA]?.seed;
  const seedB = teamData[matchup.teamB]?.seed;
  const isTossUp = matchup.winProb <= 0.60 && !matchup.locked;

  // Card border: upset = bright pink/red, toss-up = gold, override = dashed, default = subtle
  let borderColor = '#2d3348';  // default dark border
  let borderStyle = 'solid';
  if (isOverridden) borderStyle = 'dashed';

  if (matchup.isUpset) {
    borderColor = '#e84393';     // bright pink — clearly different from yellow
  } else if (isTossUp) {
    borderColor = '#f1c40f';     // bright gold/yellow
  }

  // Card background
  let bgColor = '#1e2235';
  if (matchup.locked) bgColor = 'rgba(30, 33, 48, 0.5)';
  else if (isTossUp && !matchup.isUpset) bgColor = 'rgba(241, 196, 15, 0.06)';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
      }}
    >
      {/* Main matchup card */}
      <div
        style={{
          background: bgColor,
          border: `1px ${borderStyle} ${borderColor}`,
          borderLeftWidth: (matchup.isUpset || isTossUp) ? '3px' : '1px',
          borderRadius: '6px',
          padding: '4px',
          width: '160px',
          opacity: matchup.locked ? 0.7 : 1,
        }}
        title={
          matchup.locked ? 'Locked — too lopsided to override'
          : isTossUp ? 'Toss-up — could go either way'
          : 'Click losing team to override'
        }
      >
        <TeamRow
          team={matchup.teamA}
          seed={seedA}
          isWinner={matchup.winner === matchup.teamA}
          isLocked={matchup.locked}
          winPct={matchup.winner === matchup.teamA ? matchup.winProb : 1 - matchup.winProb}
          opponent={matchup.teamB}
          onClick={() => { onOverride(mId, matchup.teamA); }}
        />
        <div style={{
          borderTop: '1px solid #2d3348',
          margin: '2px 0',
        }} />
        <TeamRow
          team={matchup.teamB}
          seed={seedB}
          isWinner={matchup.winner === matchup.teamB}
          isLocked={matchup.locked}
          winPct={matchup.winner === matchup.teamB ? matchup.winProb : 1 - matchup.winProb}
          opponent={matchup.teamA}
          onClick={() => { onOverride(mId, matchup.teamB); }}
        />
      </div>
      {/* Side icons column */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '2px',
        width: '22px',
        flexShrink: 0,
      }}>
        {isOverridden && <span title="Manual override" style={{ fontSize: '0.7rem', color: '#facc15' }}>&#9998;</span>}
        {onShowDetails && (
          <span
            onClick={(e) => { e.stopPropagation(); onShowDetails(matchup); }}
            title="View matchup details"
            style={{
              color: '#64748b',
              fontSize: '1.1rem',
              cursor: 'pointer',
              padding: '2px 4px',
              borderRadius: '4px',
              lineHeight: 1,
              transition: 'color 0.15s, background 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = '#e2e8f0';
              e.currentTarget.style.background = 'rgba(255,255,255,0.12)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = '#64748b';
              e.currentTarget.style.background = 'transparent';
            }}
          >
            &#x2139;
          </span>
        )}
      </div>
    </div>
  );
}
