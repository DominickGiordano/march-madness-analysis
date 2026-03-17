export interface BracketData {
  meta: {
    nSims: number;
    timestamp: string;
    totalTeams: number;
    lockThreshold: number;
  };
  bracket: {
    regions: Record<string, Record<string, string>>;
  };
  strategies: {
    safe: StrategyBracket;
    balanced: StrategyBracket;
    risky: StrategyBracket;
  };
  variants?: BracketVariant[];
  probMatrix: Record<string, number>;
  teamData: Record<string, TeamMetrics>;
  advancement: Record<string, AdvancementProbs>;
  upsetAlerts: UpsetAlert[];
}

export interface AdvancementProbs {
  s16: number;
  e8: number;
  f4: number;
  champ: number;
}

export interface StrategyBracket {
  champion: string;
  championConfidence: number;
  runnerUp: string;
  finalFour: string[];
  regionWinners: Record<string, string>;
  strategy: string;
  rounds: Record<string, Record<string, Matchup[]> | Matchup[]>;
}

export interface Matchup {
  teamA: string;
  teamB: string;
  winner: string;
  winProb: number;
  round: number;
  isUpset: boolean;
  locked: boolean;
}

export interface TeamMetrics {
  rank: number;
  adj_o: number;
  adj_o_rank: number;
  adj_d: number;
  adj_d_rank: number;
  barthag: number;
  barthag_rank: number;
  seed: number;
  win_pct: number;
  sos_proxy: number;
  momentum: number;
}

export interface UpsetAlert {
  region: string;
  higherSeed: number;
  higherTeam: string;
  lowerSeed: number;
  lowerTeam: string;
  reasons: string[];
  confidence: number;
  matchup: string;
}

export type StrategyKey = 'safe' | 'balanced' | 'risky';

export interface BracketVariant extends StrategyBracket {
  variantId: number;
  variantRank: number;
  color: string;
  label: string;
  upsetCount: number;
  totalLogProb: number;
}
