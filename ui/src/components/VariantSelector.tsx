import type { BracketVariant } from '../types';

const VARIANT_COLORS: string[] = [
  // safe (0-4): greens, darkest first
  '#1a5c2a', '#22763a', '#2a904a', '#32aa5a', '#3ac46a',
  // balanced (5-9): ambers
  '#8a6d1b', '#a07d20', '#b68d25', '#cc9d2a', '#e2ad2f',
  // risky (10-14): reds
  '#8a1b1b', '#a02020', '#b62525', '#cc2a2a', '#e22f2f',
];

interface Props {
  variants: BracketVariant[];
  activeId: number;
  onChange: (id: number) => void;
}

export function VariantSelector({ variants, activeId, onChange }: Props) {
  return (
    <div style={{
      display: 'flex',
      gap: '4px',
      overflowX: 'auto',
      padding: '4px 0',
      maxWidth: '100%',
      WebkitOverflowScrolling: 'touch',
    }}>
      {variants.map((v) => {
        const isActive = v.variantId === activeId;
        const bg = VARIANT_COLORS[v.variantId] ?? '#555';
        return (
          <button
            key={v.variantId}
            onClick={() => { onChange(v.variantId); }}
            title={`${v.label} — ${v.upsetCount} upsets`}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '6px 12px',
              borderRadius: '8px',
              border: isActive ? '2px solid #fff' : '2px solid transparent',
              background: bg,
              color: '#fff',
              fontWeight: isActive ? 700 : 500,
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap',
              flexShrink: 0,
              boxShadow: isActive ? `0 0 10px ${bg}88` : 'none',
              opacity: isActive ? 1 : 0.8,
              minWidth: '72px',
            }}
          >
            <span>{v.label}</span>
            <span style={{ fontSize: '0.65rem', opacity: 0.85, marginTop: '1px' }}>
              {v.upsetCount} upset{v.upsetCount !== 1 ? 's' : ''}
            </span>
          </button>
        );
      })}
    </div>
  );
}
