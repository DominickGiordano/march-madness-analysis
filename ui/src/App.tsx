import { useState, useCallback } from 'react';
import { useBracketData } from './hooks/useBracketData';
import { useBracketState } from './hooks/useBracketState';
import { VariantSelector } from './components/VariantSelector';
import { StrategyToggle } from './components/StrategyToggle';
import { ChampionBanner } from './components/ChampionBanner';
import { GameInsights } from './components/GameInsights';
import { Bracket } from './components/Bracket';
import { BracketLegend } from './components/BracketLegend';
import { MatchupModal } from './components/MatchupModal';
import { UpsetModal } from './components/UpsetModal';
import type { BracketData, StrategyKey, Matchup, UpsetAlert } from './types';

type ModalState =
  | { kind: 'none' }
  | { kind: 'matchup'; matchup: Matchup }
  | { kind: 'upset'; alert: UpsetAlert };

function AppContent({ data }: { data: BracketData }) {
  const state = useBracketState(data);
  const [modal, setModal] = useState<ModalState>({ kind: 'none' });

  const hasVariants = Boolean(data.variants && data.variants.length > 0);
  const activeVariant = hasVariants && data.variants
    ? data.variants[state.activeVariantId]
    : undefined;

  const closeModal = useCallback(() => { setModal({ kind: 'none' }); }, []);

  const openMatchupModal = useCallback((matchup: Matchup) => {
    setModal({ kind: 'matchup', matchup });
  }, []);

  const openUpsetModal = useCallback((alert: UpsetAlert) => {
    setModal({ kind: 'upset', alert });
  }, []);

  return (
    <div style={{ padding: '20px 24px', maxWidth: '100%' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px',
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
      </div>

      {/* Variant Selector or fallback Strategy Toggle */}
      <div style={{ marginBottom: '16px' }}>
        {hasVariants && data.variants ? (
          <VariantSelector
            variants={data.variants}
            activeId={state.activeVariantId}
            onChange={state.setVariant}
          />
        ) : (
          <StrategyToggle
            active={state.activeStrategy as StrategyKey}
            onChange={(s) => {
              const id = s === 'safe' ? 0 : s === 'balanced' ? 7 : 10;
              state.setVariant(id);
            }}
          />
        )}
      </div>

      {/* Champion Banner */}
      <div style={{ marginBottom: '16px' }}>
        <ChampionBanner
          bracket={state.computedBracket}
          advancement={data.advancement}
          variant={activeVariant}
          teamData={data.teamData}
        />
      </div>

      {/* Game Insights: Upset Picks / Toss-Ups / Alerts */}
      <div style={{ marginBottom: '16px' }}>
        <GameInsights
          bracket={state.computedBracket}
          alerts={data.upsetAlerts}
          teamData={data.teamData}
          onShowUpsetDetails={openUpsetModal}
          onShowMatchupDetails={openMatchupModal}
        />
      </div>

      {/* Legend + Bracket */}
      <BracketLegend />
      <Bracket
        bracket={state.computedBracket}
        regionNames={state.regionNames}
        overrides={state.overrides}
        teamData={data.teamData}
        onOverride={state.addOverride}
        onShowMatchupDetails={openMatchupModal}
      />

      {/* Modals */}
      {modal.kind === 'matchup' && (
        <MatchupModal
          matchup={modal.matchup}
          teamData={data.teamData}
          onClose={closeModal}
        />
      )}
      {modal.kind === 'upset' && (
        <UpsetModal
          alert={modal.alert}
          teamData={data.teamData}
          onClose={closeModal}
        />
      )}
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
