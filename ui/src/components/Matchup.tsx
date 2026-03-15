import type { Matchup as MatchupType, TeamMetrics } from '../types';

interface Props {
  matchup: MatchupType;
  matchupId: string;
  isOverridden: boolean;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
}

function seedColor(seed: number): string {
  if (seed <= 4) return 'var(--seed-blue)';
  if (seed <= 8) return 'var(--seed-grey)';
  if (seed <= 12) return 'var(--seed-orange)';
  return 'var(--seed-red)';
}

function probColor(prob: number): string {
  if (prob >= 0.7) return 'var(--accent-green)';
  if (prob >= 0.5) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

function TeamRow({
  team,
  seed,
  isWinner,
  isLocked,
  onClick,
}: {
  team: string;
  seed: number | undefined;
  isWinner: boolean;
  isLocked: boolean;
  onClick: () => void;
}) {
  return (
    <div
      onClick={isLocked || isWinner ? undefined : onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '3px 6px',
        borderRadius: '4px',
        background: isWinner ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
        cursor: isLocked || isWinner ? 'default' : 'pointer',
        transition: 'background 0.1s',
      }}
      onMouseEnter={(e) => {
        if (!isLocked && !isWinner) {
          e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
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
        color: isWinner ? 'var(--text-primary)' : 'var(--text-secondary)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        maxWidth: '100px',
      }}>
        {team}
      </span>
    </div>
  );
}

export function Matchup({ matchup, matchupId: mId, isOverridden, teamData, onOverride }: Props) {
  const seedA = teamData[matchup.teamA]?.seed;
  const seedB = teamData[matchup.teamB]?.seed;

  return (
    <div
      style={{
        background: matchup.locked ? 'rgba(30, 33, 48, 0.6)' : 'var(--bg-matchup)',
        border: `1px ${isOverridden ? 'dashed' : 'solid'} ${matchup.isUpset ? 'var(--accent-orange)' : 'var(--border-default)'}`,
        borderLeftWidth: matchup.isUpset ? '3px' : '1px',
        borderRadius: '6px',
        padding: '4px',
        width: '160px',
        opacity: matchup.locked ? 0.75 : 1,
        position: 'relative',
      }}
      title={matchup.locked ? 'This matchup is too lopsided to override' : `Click losing team to override (${(matchup.winProb * 100).toFixed(0)}%)`}
    >
      <TeamRow
        team={matchup.teamA}
        seed={seedA}
        isWinner={matchup.winner === matchup.teamA}
        isLocked={matchup.locked}
        onClick={() => { onOverride(mId, matchup.teamA); }}
      />
      <div style={{
        borderTop: '1px solid var(--border-default)',
        margin: '2px 0',
      }} />
      <TeamRow
        team={matchup.teamB}
        seed={seedB}
        isWinner={matchup.winner === matchup.teamB}
        isLocked={matchup.locked}
        onClick={() => { onOverride(mId, matchup.teamB); }}
      />
      {/* Probability badge */}
      <div style={{
        position: 'absolute',
        top: '-1px',
        right: '4px',
        fontSize: '0.6rem',
        fontWeight: 600,
        color: probColor(matchup.winProb),
      }}>
        {(matchup.winProb * 100).toFixed(0)}%
      </div>
      {/* Icons */}
      <div style={{
        position: 'absolute',
        bottom: '2px',
        right: '4px',
        display: 'flex',
        gap: '3px',
        fontSize: '0.6rem',
      }}>
        {matchup.locked && <span title="Locked">&#128274;</span>}
        {isOverridden && <span title="Manual override" style={{ color: 'var(--accent-amber)' }}>&#9998;</span>}
      </div>
    </div>
  );
}
