import type { StrategyBracket, AdvancementProbs, BracketVariant } from '../types';

interface Props {
  bracket: StrategyBracket;
  advancement: Record<string, AdvancementProbs>;
  variant?: BracketVariant;
}

function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}

const BADGE_COLORS: Record<string, string> = {
  green: '#2a904a',
  amber: '#b68d25',
  red: '#b62525',
};

export function ChampionBanner({ bracket, advancement, variant }: Props) {
  const champAdv = advancement[bracket.champion];

  return (
    <div style={{
      background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary))',
      border: '1px solid var(--border-default)',
      borderRadius: '12px',
      padding: '20px 28px',
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
      </div>

      <div style={{
        width: '1px',
        height: '48px',
        background: 'var(--border-default)',
      }} />

      <div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
          Final Four
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          {[...new Set(bracket.finalFour)].map((team) => {
            const adv = advancement[team];
            return (
              <div
                key={team}
                style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '8px',
                  padding: '6px 14px',
                  textAlign: 'center',
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
  );
}
