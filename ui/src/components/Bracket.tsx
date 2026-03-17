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
  onShowMatchupDetails?: (matchup: MatchupType) => void;
}

/** Wrapper that centers only the matchup card, not the info icon beside it */
function CenteredMatchup({ matchup, mId, overrides, teamData, onOverride, onShowMatchupDetails }: {
  matchup: MatchupType;
  mId: string;
  overrides: Map<string, string>;
  teamData: Record<string, TeamMetrics>;
  onOverride: (matchupId: string, winner: string) => void;
  onShowMatchupDetails?: (matchup: MatchupType) => void;
}) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <Matchup
        matchup={matchup}
        matchupId={mId}
        isOverridden={overrides.has(mId)}
        teamData={teamData}
        onOverride={onOverride}
        onShowDetails={onShowMatchupDetails}
      />
    </div>
  );
}

export function Bracket({ bracket, regionNames, overrides, teamData, onOverride, onShowMatchupDetails }: Props) {
  const finalFour = (bracket.rounds['final_four'] ?? []) as MatchupType[];
  const championship = (bracket.rounds['championship'] ?? []) as MatchupType[];

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
              onShowMatchupDetails={onShowMatchupDetails}
            />
          );
        })}
      </div>

      {/* Center: Final Four + Championship + Champion */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '12px',
        flexShrink: 0,
        padding: '0 16px',
        minWidth: '220px',
      }}>
        {/* Final Four label */}
        <div style={{
          fontSize: '0.75rem',
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          fontWeight: 600,
        }}>
          Final Four
        </div>

        {/* Final Four games — side by side */}
        <div style={{
          display: 'flex',
          gap: '16px',
          justifyContent: 'center',
        }}>
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
                onShowDetails={onShowMatchupDetails}
              />
            );
          })}
        </div>

        {/* Championship label */}
        <div style={{
          fontSize: '0.75rem',
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          fontWeight: 600,
          marginTop: '8px',
        }}>
          Championship
        </div>

        {/* Championship game — centered on card only */}
        {championship.map((m, idx) => {
          const mId = matchupId('championship', 'championship', idx);
          return (
            <CenteredMatchup
              key={mId}
              matchup={m}
              mId={mId}
              overrides={overrides}
              teamData={teamData}
              onOverride={onOverride}
              onShowMatchupDetails={onShowMatchupDetails}
            />
          );
        })}

        {/* Champion badge — centered */}
        {championship[0] && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(139,92,246,0.2))',
            border: '1px solid #3b82f6',
            borderRadius: '10px',
            padding: '10px 28px',
            textAlign: 'center',
            marginTop: '4px',
          }}>
            <div style={{ fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Champion
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#3b82f6' }}>
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
              onShowMatchupDetails={onShowMatchupDetails}
              flip
            />
          );
        })}
      </div>
    </div>
  );
}
