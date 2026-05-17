export type TerminalLine = {
  prefix: string;
  text: string;
  color: "cyan" | "green" | "yellow" | "white" | "magenta";
  delay: number; // ms after terminal appears
};

export type DemoScript = {
  userPrompt: string;
  claudeResponse: string;
  terminalLines: TerminalLine[];
  loopIntervalMs: number;
  typingSpeedMs: number;
};

export const DEMO_SCRIPT: DemoScript = {
  userPrompt: "Refactor my auth module to use JWT, run tests, open PR",
  claudeResponse: "Spawning Maestro session on your VPS...",
  typingSpeedMs: 50,
  loopIntervalMs: 12000,
  terminalLines: [
    {
      prefix: "[maestro]",
      text: "spawning session sess_abc123 on droplet-nyc1",
      color: "cyan",
      delay: 0,
    },
    {
      prefix: "[claude]",
      text: "reading src/auth/...",
      color: "yellow",
      delay: 420,
    },
    {
      prefix: "[claude]",
      text: "writing src/auth/jwt.py",
      color: "yellow",
      delay: 900,
    },
    {
      prefix: "[claude]",
      text: "running pytest...",
      color: "yellow",
      delay: 1500,
    },
    {
      prefix: "[pytest]",
      text: "✓ 42 tests passed",
      color: "green",
      delay: 2400,
    },
    {
      prefix: "[git]",
      text: "creating branch refactor/auth-jwt-v2",
      color: "magenta",
      delay: 3000,
    },
    {
      prefix: "[gh]",
      text: "opening PR #142 to ethanadjedj-labs/myrepo",
      color: "magenta",
      delay: 3600,
    },
    {
      prefix: "✓",
      text: "Session complete — 4 min 12 sec",
      color: "green",
      delay: 4400,
    },
  ],
};
