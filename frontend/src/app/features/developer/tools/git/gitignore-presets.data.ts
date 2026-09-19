export interface GitignorePreset {
  id: string;
  label: string;
  content: string;
}

export const GITIGNORE_PRESETS: GitignorePreset[] = [
  {
    id: 'node',
    label: 'Node.js',
    content: 'node_modules/\nnpm-debug.log*\nyarn-error.log*\ndist/\n.env\n.env.local\ncoverage/',
  },
  {
    id: 'python',
    label: 'Python',
    content: '__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n*.egg-info/\ndist/\nbuild/\n.pytest_cache/',
  },
  {
    id: 'java',
    label: 'Java',
    content: '*.class\ntarget/\n.gradle/\nbuild/\n*.jar\n*.war\nhs_err_pid*',
  },
  {
    id: 'go',
    label: 'Go',
    content: '*.exe\n*.test\n*.out\nvendor/\n/bin/',
  },
  {
    id: 'rust',
    label: 'Rust',
    content: '/target/\nCargo.lock',
  },
  {
    id: 'macos',
    label: 'macOS',
    content: '.DS_Store\n.AppleDouble\n.LSOverride\nIcon\n._*',
  },
  {
    id: 'windows',
    label: 'Windows',
    content: 'Thumbs.db\nehthumbs.db\nDesktop.ini\n$RECYCLE.BIN/',
  },
  {
    id: 'vscode',
    label: 'VS Code',
    content: '.vscode/\n!.vscode/extensions.json',
  },
  {
    id: 'intellij',
    label: 'IntelliJ / JetBrains',
    content: '.idea/\n*.iml\n*.iws',
  },
];
