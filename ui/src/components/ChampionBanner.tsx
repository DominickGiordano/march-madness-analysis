import type { StrategyBracket, AdvancementProbs, BracketVariant, Matchup, TeamMetrics } from '../types';

interface Props {
  bracket: StrategyBracket;
  advancement: Record<string, AdvancementProbs>;
  variant?: BracketVariant;
  teamData?: Record<string, TeamMetrics>;
}

function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}

const BADGE_COLORS: Record<string, string> = {
  green: '#2a904a',
  amber: '#b68d25',
  red: '#b62525',
};

const ROUND_ORDER = ['r64', 'r32', 'sweet_16', 'elite_8'] as const;
const ROUND_LABELS: Record<string, string> = {
  r64: 'R64',
  r32: 'R32',
  sweet_16: 'S16',
  elite_8: 'E8',
  final_four: 'FF',
  championship: 'Final',
};

function buildTeamPath(
  team: string,
  rounds: StrategyBracket['rounds'],
): { round: string; opponent: string }[] {
  const path: { round: string; opponent: string }[] = [];

  // Search region rounds
  for (const regionKey of Object.keys(rounds)) {
    const regionData = rounds[regionKey];
    if (!regionData || Array.isArray(regionData)) continue;

    const regionRounds = regionData as Record<string, Matchup[]>;
    for (const roundKey of ROUND_ORDER) {
      const matchups = regionRounds[roundKey];
      if (!matchups) continue;
      for (const m of matchups) {
        if (m.winner === team && (m.teamA === team || m.teamB === team)) {
          const opponent = m.teamA === team ? m.teamB : m.teamA;
          path.push({ round: ROUND_LABELS[roundKey] ?? roundKey, opponent });
        }
      }
    }
  }

  // Final four
  const ff = rounds['final_four'];
  if (ff && Array.isArray(ff)) {
    for (const m of ff as Matchup[]) {
      if (m.winner === team && (m.teamA === team || m.teamB === team)) {
        const opponent = m.teamA === team ? m.teamB : m.teamA;
        path.push({ round: 'FF', opponent });
      }
    }
  }

  // Championship
  const champ = rounds['championship'];
  if (champ && Array.isArray(champ)) {
    for (const m of champ as Matchup[]) {
      if (m.winner === team && (m.teamA === team || m.teamB === team)) {
        const opponent = m.teamA === team ? m.teamB : m.teamA;
        path.push({ round: 'Final', opponent });
      }
    }
  }

  return path;
}

export function ChampionBanner({ bracket, advancement, variant, teamData }: Props) {
  const champAdv = advancement[bracket.champion];
  const champMetrics = teamData?.[bracket.champion];
  const champPath = buildTeamPath(bracket.champion, bracket.rounds);

  return (
    <div style={{
      background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary))',
      border: '1px solid var(--border-default)',
      borderRadius: '12px',
      padding: '20px 28px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
    }}>
      {/* Top row: champion info + final four */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '32px',
        flexWrap: 'wrap',
      }}>
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '2px',
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Predicted Champion
            </div>
            {variant && (
              <span style={{
                display: 'inline-block',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '0.65rem',
                fontWeight: 600,
                color: '#fff',
                background: BADGE_COLORS[variant.color] ?? 'var(--accent-blue)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}>
                {variant.label}
              </span>
            )}
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--accent-blue)' }}>
            {bracket.champion}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Confidence: {pct(bracket.championConfidence)} | vs {bracket.runnerUp}
            {variant != null && (
              <span style={{ marginLeft: '10px', opacity: 0.8 }}>
                | {variant.upsetCount} upset{variant.upsetCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Champion key metrics */}
          {champMetrics && (
            <div style={{
              display: 'flex',
              gap: '12px',
              marginTop: '8px',
              flexWrap: 'wrap',
            }}>
              {([
                { label: 'Barthag', value: champMetrics.barthag.toFixed(4) },
                { label: 'AdjO', value: `#${String(champMetrics.adj_o_rank)}` },
                { label: 'AdjD', value: `#${String(champMetrics.adj_d_rank)}` },
                { label: 'Win%', value: `${(champMetrics.win_pct * 100).toFixed(0)}%` },
                { label: 'Rank', value: `#${String(champMetrics.rank)}` },
              ]).map((stat) => (
                <span key={stat.label} style={{
                  fontSize: '0.7rem',
                  color: 'var(--text-muted)',
                  background: 'var(--bg-primary)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '1px solid var(--border-default)',
                }}>
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{stat.value}</span>
                  {' '}{stat.label}
                </span>
              ))}
              {champMetrics.injury_adjusted && (
                <span style={{
                  fontSize: '0.7rem',
                  color: 'var(--accent-red)',
                  background: 'rgba(239, 68, 68, 0.1)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}>
                  Injury adjusted
                </span>
              )}
            </div>
          )}
        </div>

        <div style={{ width: '1px', height: '48px', background: 'var(--border-default)' }} />

        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
            Final Four
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            {[...new Set(bracket.finalFour)].map((team) => {
              const adv = advancement[team];
              const teamPath = buildTeamPath(team, bracket.rounds);
              const pathStr = teamPath.map((p) => `${p.round}: vs ${p.opponent}`).join(' > ');
              return (
                <div
                  key={team}
                  title={pathStr}
                  style={{
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-default)',
                    borderRadius: '8px',
                    padding: '6px 14px',
                    textAlign: 'center',
                    cursor: 'default',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{team}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    F4: {adv ? pct(adv.f4) : '---'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {champAdv && (
          <>
            <div style={{ width: '1px', height: '48px', background: 'var(--border-default)' }} />
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              <div>S16: {pct(champAdv.s16)} | E8: {pct(champAdv.e8)}</div>
              <div>F4: {pct(champAdv.f4)} | Champ: {pct(champAdv.champ)}</div>
            </div>
          </>
        )}
      </div>

      {/* Tournament path */}
      {champPath.length > 0 && (
        <div style={{
          borderTop: '1px solid var(--border-default)',
          paddingTop: '12px',
        }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            Champion Path
          </div>
          <div style={{
            display: 'flex',
            gap: '4px',
            flexWrap: 'wrap',
            alignItems: 'center',
          }}>
            {champPath.map((step, idx) => (
              <span key={step.round} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                {idx > 0 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>&#x2192;</span>
                )}
                <span style={{
                  fontSize: '0.75rem',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-default)',
                }}>
                  <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>{step.round}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{': vs '}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{step.opponent}</span>
                </span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
