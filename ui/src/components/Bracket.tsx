import type { StrategyBracket, Matchup as MatchupType, TeamMetrics } from '../types';
import { Region } from './Region';
import { Matchup } from './Matchup';
import { matchupId } from '../lib/cascade';

interface Props {
  bracket: StrategyBracket;
  regionNames: string[];
  overrides: Map<string, string>;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
}

export function Bracket({ bracket, regionNames, overrides, teamData, onOverride }: Props) {
  const finalFour = (bracket.rounds['final_four'] ?? []) as MatchupType[];
  const championship = (bracket.rounds['championship'] ?? []) as MatchupType[];

  // Regions: left side = [0,1], right side = [2,3]
  const leftRegions = regionNames.slice(0, 2);
  const rightRegions = regionNames.slice(2, 4);

  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      alignItems: 'center',
      overflowX: 'auto',
      padding: '16px 0',
    }}>
      {/* Left side regions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', flexShrink: 0 }}>
        {leftRegions.map((region) => {
          const regionRounds = bracket.rounds[region];
          if (!regionRounds || Array.isArray(regionRounds)) return null;
          return (
            <Region
              key={region}
              regionName={region}
              rounds={regionRounds as Record<string, MatchupType[]>}
              overrides={overrides}
              teamData={teamData}
              onOverride={onOverride}
            />
          );
        })}
      </div>

      {/* Center: Final Four + Championship */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '16px',
        flexShrink: 0,
        padding: '0 16px',
        minWidth: '200px',
      }}>
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontWeight: 600,
        }}>
          Final Four
        </div>

        {finalFour.map((m, idx) => {
          const mId = matchupId('final_four', 'final_four', idx);
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

        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          fontWeight: 600,
          marginTop: '8px',
        }}>
          Championship
        </div>

        {championship.map((m, idx) => {
          const mId = matchupId('championship', 'championship', idx);
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

        {championship[0] && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))',
            border: '1px solid var(--accent-blue)',
            borderRadius: '8px',
            padding: '8px 20px',
            textAlign: 'center',
            marginTop: '4px',
          }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Champion</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
              {championship[0].winner}
            </div>
          </div>
        )}
      </div>

      {/* Right side regions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', flexShrink: 0 }}>
        {rightRegions.map((region) => {
          const regionRounds = bracket.rounds[region];
          if (!regionRounds || Array.isArray(regionRounds)) return null;
          return (
            <Region
              key={region}
              regionName={region}
              rounds={regionRounds as Record<string, MatchupType[]>}
              overrides={overrides}
              teamData={teamData}
              onOverride={onOverride}
              flip
            />
          );
        })}
      </div>
    </div>
  );
}
