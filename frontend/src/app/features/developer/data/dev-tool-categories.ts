import { DevToolCategory } from '../models/dev-tool.model';

export const DEV_TOOL_CATEGORIES: DevToolCategory[] = [
  { id: 'encoding', label: 'Encoding & Decoding', description: 'Convert text between common encodings.', icon: 'binary' },
  { id: 'json', label: 'JSON Tools', description: 'Format, validate, and convert JSON.', icon: 'file-json' },
  { id: 'xml-yaml', label: 'XML / YAML Tools', description: 'Format, validate, and convert XML and YAML.', icon: 'file-code' },
  { id: 'hashing', label: 'Hashing & Cryptography', description: 'Generate hashes and HMACs locally.', icon: 'hash' },
  { id: 'generators', label: 'Generators', description: 'Generate UUIDs, passwords, and test data.', icon: 'wand' },
  { id: 'datetime', label: 'Date & Time', description: 'Convert and inspect timestamps, cron, and timezones.', icon: 'calendar-clock' },
  { id: 'web', label: 'Web Development', description: 'Format, minify, and inspect front-end code.', icon: 'square-code' },
  { id: 'sql', label: 'SQL Tools', description: 'Format, validate, and inspect SQL — no database connection.', icon: 'database' },
  { id: 'dev-utils', label: 'Developer Utilities', description: 'Diffing, counting, and text utilities.', icon: 'wrench' },
  { id: 'network', label: 'Network Utilities', description: 'Look up, parse, and calculate networking values.', icon: 'network' },
  { id: 'git', label: 'Git Tools', description: 'Generate git commands, .gitignore files, and commit messages.', icon: 'git-branch' },
  { id: 'code-gen', label: 'Code Generators', description: 'Generate typed models from JSON in several languages.', icon: 'file-code-2' },
  { id: 'security', label: 'Security Utilities', description: 'Check passwords, inspect tokens, generate security headers.', icon: 'shield' },
  { id: 'data-conversion', label: 'Data Conversion', description: 'Convert between data formats and encodings.', icon: 'repeat' },
];
