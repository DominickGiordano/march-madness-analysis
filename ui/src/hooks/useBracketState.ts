import { useState, useMemo, useCallback } from 'react';
import type { BracketData, StrategyBracket, StrategyKey } from '../types';
import { applyOverrides } from '../lib/cascade';

export interface BracketState {
  activeStrategy: StrategyKey;
  overrides: Map<string, string>;
  computedBracket: StrategyBracket;
  regionNames: string[];
  setStrategy: (s: StrategyKey) => void;
  addOverride: (matchupId: string, winner: string) => void;
  hasOverrides: boolean;
}

export function useBracketState(data: BracketData): BracketState {
  const [activeStrategy, setActiveStrategy] = useState<StrategyKey>('balanced');
  const [overrides, setOverrides] = useState<Map<string, string>>(new Map());

  const regionNames = useMemo(
    () => Object.keys(data.bracket.regions),
    [data.bracket.regions],
  );

  const baseBracket = data.strategies[activeStrategy];

  const computedBracket = useMemo(
    () => applyOverrides(baseBracket, overrides, data.probMatrix, regionNames),
    [baseBracket, overrides, data.probMatrix, regionNames],
  );

  const setStrategy = useCallback(
    (s: StrategyKey) => {
      if (s === activeStrategy) return;
      if (overrides.size > 0) {
        const confirmed = window.confirm(
          'Switching strategies will reset your manual picks. Continue?',
        );
        if (!confirmed) return;
      }
      setOverrides(new Map());
      setActiveStrategy(s);
    },
    [activeStrategy, overrides.size],
  );

  const addOverride = useCallback((matchupId: string, winner: string) => {
    setOverrides((prev) => {
      const next = new Map(prev);
      next.set(matchupId, winner);
      return next;
    });
  }, []);

  return {
    activeStrategy,
    overrides,
    computedBracket,
    regionNames,
    setStrategy,
    addOverride,
    hasOverrides: overrides.size > 0,
  };
}
