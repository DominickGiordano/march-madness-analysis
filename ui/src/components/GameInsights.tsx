import { useState } from 'react';
import type { UpsetAlert, Matchup, StrategyBracket, TeamMetrics } from '../types';

interface Props {
  bracket: StrategyBracket;
  alerts: UpsetAlert[];
  teamData: Record<string, TeamMetrics>;
  onShowUpsetDetails?: (alert: UpsetAlert) => void;
  onShowMatchupDetails?: (matchup: Matchup) => void;
}

type Tab = 'upsets' | 'tossups' | 'alerts';

function getAllMatchups(bracket: StrategyBracket): Matchup[] {
  const all: Matchup[] = [];
  const rounds = bracket.rounds;
  for (const regionData of Object.values(rounds)) {
    if (Array.isArray(regionData)) {
      for (const m of regionData) {
        if (m && typeof m === 'object' && 'teamA' in m) all.push(m as Matchup);
      }
    } else if (regionData && typeof regionData === 'object') {
      for (const matchups of Object.values(regionData)) {
        if (Array.isArray(matchups)) {
          for (const m of matchups) {
            if (m && typeof m === 'object' && 'teamA' in m) all.push(m as Matchup);
          }
        }
      }
    }
  }
  return all;
}

const ROUND_LABELS: Record<number, string> = {
  1: 'R64', 2: 'R32', 3: 'S16', 4: 'E8', 5: 'F4', 6: 'Championship',
};

export function GameInsights({ bracket, alerts, teamData, onShowUpsetDetails, onShowMatchupDetails }: Props) {
  const [collapsed, setCollapsed] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('upsets');

  const allMatchups = getAllMatchups(bracket);

  // Upset picks: bracket picked the lower seed to win
  const upsetPicks = allMatchups.filter((m) => m.isUpset);

  // Toss-ups: winner has ≤60% BUT it's NOT an upset pick (favorite was kept)
  const tossUps = allMatchups.filter((m) =>
    m.winProb <= 0.60 && !m.locked && !m.isUpset
  );

  // Sort both by probability (closest games first)
  upsetPicks.sort((a, b) => a.winProb - b.winProb);
  tossUps.sort((a, b) => a.winProb - b.winProb);

  const tabs: { key: Tab; label: string; count: number; color: string }[] = [
    { key: 'upsets', label: 'Upset Picks', count: upsetPicks.length, color: '#e84393' },
    { key: 'tossups', label: 'Toss-Ups', count: tossUps.length, color: '#f1c40f' },
    { key: 'alerts', label: 'Upset Alerts', count: alerts.length, color: '#f97316' },
  ];

  return (
    <div style={{
      background: '#161929',
      border: '1px solid #2d3348',
      borderRadius: '12px',
      overflow: 'hidden',
    }}>
      {/* Collapsible header */}
      <button
        onClick={() => { setCollapsed(!collapsed); }}
        style={{
          width: '100%',
          padding: '10px 16px',
          background: 'none',
          border: 'none',
          borderBottom: collapsed ? 'none' : '1px solid #2d3348',
          color: '#e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.9rem',
          fontWeight: 600,
          cursor: 'pointer',
        }}
      >
        <span>
          Game Insights
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 400, marginLeft: '12px' }}>
            {String(upsetPicks.length)} upsets &middot; {String(tossUps.length)} toss-ups &middot; {String(alerts.length)} alerts
          </span>
        </span>
        <span style={{ color: '#64748b', fontSize: '0.75rem' }}>
          {collapsed ? '▼ Show' : '▲ Hide'}
        </span>
      </button>

      {!collapsed && <>
      {/* Tab bar */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #2d3348',
      }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); }}
            style={{
              flex: 1,
              padding: '10px 16px',
              background: activeTab === tab.key ? '#1e2235' : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.key ? `2px solid ${tab.color}` : '2px solid transparent',
              color: activeTab === tab.key ? '#e2e8f0' : '#64748b',
              fontSize: '0.85rem',
              fontWeight: activeTab === tab.key ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.15s',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {tab.label}
            <span style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              background: activeTab === tab.key ? tab.color : '#2d3348',
              color: activeTab === tab.key ? '#fff' : '#94a3b8',
              padding: '1px 7px',
              borderRadius: '10px',
            }}>
              {String(tab.count)}
            </span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ padding: '12px 16px', maxHeight: '300px', overflowY: 'auto' }}>
        {activeTab === 'upsets' && (
          upsetPicks.length === 0
            ? <EmptyState text="No upsets picked in this bracket variant." />
            : <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 10px', lineHeight: '1.4' }}>
                  Games where this bracket picks the lower seed to win. These are your differentiation plays.
                </p>
                {upsetPicks.map((m) => (
                  <MatchupRow
                    key={`${m.teamA}-${m.teamB}`}
                    matchup={m}
                    teamData={teamData}
                    borderColor="#e84393"
                    onClick={() => { onShowMatchupDetails?.(m); }}
                  />
                ))}
              </div>
        )}

        {activeTab === 'tossups' && (
          tossUps.length === 0
            ? <EmptyState text="No toss-up games in this bracket — all matchups are decisive." />
            : <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 10px', lineHeight: '1.4' }}>
                  Games where the favorite has ≤60% chance but is still picked. Consider flipping these for differentiation.
                </p>
                {tossUps.map((m) => (
                  <MatchupRow
                    key={`${m.teamA}-${m.teamB}`}
                    matchup={m}
                    teamData={teamData}
                    borderColor="#f1c40f"
                    onClick={() => { onShowMatchupDetails?.(m); }}
                  />
                ))}
              </div>
        )}

        {activeTab === 'alerts' && (
          alerts.length === 0
            ? <EmptyState text="No upset alerts detected." />
            : <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 10px', lineHeight: '1.4' }}>
                  Model-detected upset potential based on Barthag, defense, seed history, and momentum.
                </p>
                {alerts.map((alert) => (
                  <AlertRow
                    key={alert.matchup}
                    alert={alert}
                    onClick={() => { onShowUpsetDetails?.(alert); }}
                  />
                ))}
              </div>
        )}
      </div>
      </>}
    </div>
  );
}

function MatchupRow({ matchup, teamData, borderColor, onClick }: {
  matchup: Matchup;
  teamData: Record<string, TeamMetrics>;
  borderColor: string;
  onClick: () => void;
}) {
  const seedA = teamData[matchup.teamA]?.seed;
  const seedB = teamData[matchup.teamB]?.seed;
  const winnerSeed = matchup.winner === matchup.teamA ? seedA : seedB;
  const loserSeed = matchup.winner === matchup.teamA ? seedB : seedA;
  const loser = matchup.winner === matchup.teamA ? matchup.teamB : matchup.teamA;

  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 12px',
        background: '#1a1d2e',
        borderLeft: `3px solid ${borderColor}`,
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'background 0.15s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = '#222640'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = '#1a1d2e'; }}
    >
      <div style={{ flex: 1 }}>
        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#e2e8f0' }}>
          #{winnerSeed} {matchup.winner}
        </span>
        <span style={{ color: '#64748b', fontSize: '0.8rem' }}>
          {' '}over #{loserSeed} {loser}
        </span>
        <span style={{ color: '#4a5568', fontSize: '0.75rem', marginLeft: '8px' }}>
          {ROUND_LABELS[matchup.round] ?? `R${String(matchup.round)}`}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{
          fontSize: '0.85rem',
          fontWeight: 700,
          color: matchup.winProb >= 0.7 ? '#4ade80' : matchup.winProb >= 0.5 ? '#facc15' : '#f87171',
        }}>
          {(matchup.winProb * 100).toFixed(0)}%
        </span>
        <span style={{ fontSize: '0.65rem', color: '#64748b' }}>&#x2192;</span>
      </div>
    </div>
  );
}

function AlertRow({ alert, onClick }: { alert: UpsetAlert; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 12px',
        background: '#1a1d2e',
        borderLeft: '3px solid #f97316',
        borderRadius: '6px',
        cursor: 'pointer',
        transition: 'background 0.15s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = '#222640'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = '#1a1d2e'; }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#e2e8f0' }}>
          {alert.matchup}
          <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize' }}>
            ({alert.region})
          </span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
          {alert.reasons.map((r) => (
            <span key={r} style={{
              fontSize: '0.65rem',
              background: '#2d3348',
              padding: '1px 6px',
              borderRadius: '3px',
              color: '#94a3b8',
            }}>
              {r}
            </span>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{
          fontSize: '0.85rem',
          fontWeight: 700,
          color: alert.confidence >= 0.7 ? '#4ade80' : alert.confidence >= 0.5 ? '#facc15' : '#f87171',
        }}>
          {(alert.confidence * 100).toFixed(0)}%
        </span>
        <span style={{ fontSize: '0.65rem', color: '#64748b' }}>&#x2192;</span>
      </div>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <p style={{ fontSize: '0.8rem', color: '#64748b', textAlign: 'center', padding: '20px 0' }}>
      {text}
    </p>
  );
}
