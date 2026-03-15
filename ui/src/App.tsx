import { useBracketData } from './hooks/useBracketData';
import { useBracketState } from './hooks/useBracketState';
import { StrategyToggle } from './components/StrategyToggle';
import { ChampionBanner } from './components/ChampionBanner';
import { UpsetAlerts } from './components/UpsetAlerts';
import { Bracket } from './components/Bracket';

function AppContent({ data }: { data: import('./types').BracketData }) {
  const state = useBracketState(data);

  return (
    <div style={{ padding: '20px 24px', maxWidth: '100%' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>
            March Madness Bracket Analysis
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '2px 0 0' }}>
            {data.meta.nSims.toLocaleString()} simulations | {data.meta.timestamp.split('T')[0]}
            {state.hasOverrides && (
              <span style={{ color: 'var(--accent-amber)', marginLeft: '12px' }}>
                &#9998; Manual overrides active
              </span>
            )}
          </p>
        </div>
        <StrategyToggle active={state.activeStrategy} onChange={state.setStrategy} />
      </div>

      {/* Champion Banner */}
      <div style={{ marginBottom: '16px' }}>
        <ChampionBanner bracket={state.computedBracket} advancement={data.advancement} />
      </div>

      {/* Upset Alerts */}
      <div style={{ marginBottom: '16px' }}>
        <UpsetAlerts alerts={data.upsetAlerts} />
      </div>

      {/* Bracket */}
      <Bracket
        bracket={state.computedBracket}
        regionNames={state.regionNames}
        overrides={state.overrides}
        teamData={data.teamData}
        onOverride={state.addOverride}
      />
    </div>
  );
}

export default function App() {
  const { data, loading, error } = useBracketData();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        color: 'var(--text-secondary)',
        fontSize: '1.1rem',
      }}>
        Loading bracket data...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        color: 'var(--accent-red)',
        fontSize: '1.1rem',
      }}>
        Error: {error ?? 'No data loaded'}
      </div>
    );
  }

  return <AppContent data={data} />;
}
