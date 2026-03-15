import type { StrategyKey } from '../types';

const STRATEGIES: { key: StrategyKey; label: string; desc: string }[] = [
  { key: 'safe', label: 'Safe', desc: 'Chalk picks, favor higher seeds' },
  { key: 'balanced', label: 'Balanced', desc: 'Mix of chalk and value upsets' },
  { key: 'risky', label: 'Risky', desc: 'Maximize upsets for pool differentiation' },
];

interface Props {
  active: StrategyKey;
  onChange: (s: StrategyKey) => void;
}

export function StrategyToggle({ active, onChange }: Props) {
  return (
    <div style={{
      display: 'flex',
      gap: '2px',
      background: 'var(--bg-tertiary)',
      borderRadius: '8px',
      padding: '3px',
    }}>
      {STRATEGIES.map((s) => (
        <button
          key={s.key}
          onClick={() => { onChange(s.key); }}
          title={s.desc}
          style={{
            padding: '8px 20px',
            borderRadius: '6px',
            border: 'none',
            background: active === s.key ? 'var(--accent-blue)' : 'transparent',
            color: active === s.key ? '#fff' : 'var(--text-secondary)',
            fontWeight: active === s.key ? 600 : 400,
            fontSize: '0.9rem',
            transition: 'all 0.15s ease',
          }}
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
