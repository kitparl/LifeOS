import { DevToolMeta } from '../models/dev-tool.model';

/**
 * Full tool catalog for the Developer module. A tool the PRD lists under more than one
 * category (e.g. Regex Tester, JWT Decoder, Hash Generator) is implemented once and
 * appears under every category it's listed in via `categories`.
 */
export const DEV_TOOLS: DevToolMeta[] = [
  // --- Encoding & Decoding ---
  { id: 'base64', name: 'Base64 Encode / Decode', description: 'Convert text to and from Base64.', route: 'base64', icon: 'binary', categories: ['encoding'], keywords: ['base64', 'encode', 'decode'] },
  { id: 'url-encoder', name: 'URL Encode / Decode', description: 'Percent-encode or decode a URL or URI component.', route: 'url-encoder', icon: 'link', categories: ['encoding'], keywords: ['url', 'uri', 'percent encoding', 'encode', 'decode'] },
  { id: 'html-encoder', name: 'HTML Encode / Decode', description: 'Convert text to and from HTML entities.', route: 'html-encoder', icon: 'code', categories: ['encoding'], keywords: ['html', 'entities', 'escape', 'encode', 'decode'] },
  { id: 'jwt-decoder', name: 'JWT Decode / Inspector', description: 'Decode a JSON Web Token and inspect its header, payload, and expiry.', route: 'jwt-decoder', icon: 'key-round', categories: ['encoding', 'security'], keywords: ['jwt', 'token', 'decode', 'auth', 'jwt inspector'] },
  { id: 'hex-text', name: 'Hex ↔ Text', description: 'Convert between hexadecimal and plain text.', route: 'hex-text', icon: 'hash', categories: ['encoding'], keywords: ['hex', 'hexadecimal', 'text'] },
  { id: 'binary-text', name: 'Binary ↔ Text', description: 'Convert between binary (0/1) and plain text.', route: 'binary-text', icon: 'binary', categories: ['encoding'], keywords: ['binary', 'text', 'bits'] },
  { id: 'ascii-text', name: 'ASCII ↔ Text', description: 'Convert between ASCII codes and plain text.', route: 'ascii-text', icon: 'type', categories: ['encoding'], keywords: ['ascii', 'text', 'codes'] },
  { id: 'unicode-converter', name: 'Unicode Converter', description: 'Convert text to and from Unicode escape sequences and code points.', route: 'unicode-converter', icon: 'globe', categories: ['encoding'], keywords: ['unicode', 'utf-8', 'code point', 'escape'] },
  { id: 'base32', name: 'Base32 Encode / Decode', description: 'Convert text to and from Base32 (RFC 4648).', route: 'base32', icon: 'binary', categories: ['encoding'], keywords: ['base32', 'encode', 'decode'] },
  { id: 'base58', name: 'Base58 Encode / Decode', description: 'Convert text to and from Base58 (Bitcoin alphabet).', route: 'base58', icon: 'binary', categories: ['encoding'], keywords: ['base58', 'encode', 'decode', 'bitcoin'] },

  // --- JSON Tools ---
  { id: 'json-formatter', name: 'JSON Formatter', description: 'Pretty-print JSON with configurable indentation.', route: 'json-formatter', icon: 'braces', categories: ['json'], keywords: ['json', 'format', 'prettify', 'indent'] },
  { id: 'json-validator', name: 'JSON Validator', description: 'Validate JSON and get a precise error location.', route: 'json-validator', icon: 'braces', categories: ['json'], keywords: ['json', 'validate', 'lint'] },
  { id: 'json-minifier', name: 'JSON Minifier', description: 'Minify JSON by removing whitespace.', route: 'json-minifier', icon: 'braces', categories: ['json'], keywords: ['json', 'minify', 'compress'] },
  { id: 'csv-json', name: 'CSV ↔ JSON', description: 'Convert between CSV and JSON.', route: 'csv-json', icon: 'table-properties', categories: ['json', 'data-conversion'], keywords: ['csv', 'json', 'convert', 'spreadsheet'] },
  { id: 'json-to-yaml', name: 'JSON → YAML', description: 'Convert JSON to YAML.', route: 'json-to-yaml', icon: 'file-code', categories: ['json'], keywords: ['json', 'yaml', 'convert'] },
  { id: 'json-to-typescript', name: 'JSON → TypeScript', description: 'Generate a TypeScript interface or type from JSON.', route: 'json-to-typescript', icon: 'file-code-2', categories: ['json', 'code-gen'], keywords: ['json', 'typescript', 'interface', 'type', 'codegen'] },
  { id: 'jsonpath-tester', name: 'JSONPath Tester', description: 'Test a JSONPath expression against JSON data.', route: 'jsonpath-tester', icon: 'search', categories: ['json'], keywords: ['jsonpath', 'json', 'query', 'test'] },
  { id: 'json-diff', name: 'JSON Diff', description: 'Compare two JSON objects and see what changed.', route: 'json-diff', icon: 'diff', categories: ['json'], keywords: ['json', 'diff', 'compare'] },

  // --- XML / YAML Tools ---
  { id: 'xml-formatter', name: 'XML Formatter', description: 'Pretty-print XML with configurable indentation.', route: 'xml-formatter', icon: 'file-code', categories: ['xml-yaml'], keywords: ['xml', 'format', 'prettify'] },
  { id: 'xml-validator', name: 'XML Validator', description: 'Validate XML and get a clear error message.', route: 'xml-validator', icon: 'file-code', categories: ['xml-yaml'], keywords: ['xml', 'validate', 'lint'] },
  { id: 'xml-json', name: 'XML ↔ JSON', description: 'Convert between XML and JSON.', route: 'xml-json', icon: 'file-code', categories: ['xml-yaml'], keywords: ['xml', 'json', 'convert'] },
  { id: 'yaml-formatter', name: 'YAML Formatter', description: 'Pretty-print and validate YAML.', route: 'yaml-formatter', icon: 'file-code', categories: ['xml-yaml'], keywords: ['yaml', 'format', 'validate'] },
  { id: 'yaml-json', name: 'YAML ↔ JSON', description: 'Convert between YAML and JSON.', route: 'yaml-json', icon: 'file-code', categories: ['xml-yaml'], keywords: ['yaml', 'json', 'convert'] },

  // --- Hashing & Cryptography ---
  { id: 'hash-generator', name: 'Hash Generator', description: 'Generate MD5, SHA-1, SHA-256, or SHA-512 hashes locally.', route: 'hash-generator', icon: 'hash', categories: ['hashing', 'security'], keywords: ['md5', 'sha1', 'sha-1', 'sha256', 'sha-256', 'sha512', 'sha-512', 'hash', 'checksum'] },
  { id: 'hmac-generator', name: 'HMAC Generator', description: 'Generate an HMAC using a secret key.', route: 'hmac-generator', icon: 'key-round', categories: ['hashing'], keywords: ['hmac', 'hash', 'secret', 'signature'] },

  // --- Generators ---
  { id: 'uuid-generator', name: 'UUID Generator', description: 'Generate UUID v4 or v7 identifiers.', route: 'uuid-generator', icon: 'fingerprint', categories: ['generators'], keywords: ['uuid', 'guid', 'v4', 'v7', 'identifier'] },
  { id: 'random-string-generator', name: 'Random String Generator', description: 'Generate a random string with a chosen character set and length.', route: 'random-string-generator', icon: 'shuffle', categories: ['generators'], keywords: ['random', 'string', 'generate'] },
  { id: 'password-generator', name: 'Password Generator', description: 'Generate a strong random password.', route: 'password-generator', icon: 'lock', categories: ['generators'], keywords: ['password', 'generate', 'secure'] },
  { id: 'lorem-ipsum-generator', name: 'Lorem Ipsum Generator', description: 'Generate placeholder text.', route: 'lorem-ipsum-generator', icon: 'text', categories: ['generators'], keywords: ['lorem', 'ipsum', 'placeholder', 'text'] },
  { id: 'fake-json-generator', name: 'Fake JSON Data Generator', description: 'Generate fake JSON data from a template.', route: 'fake-json-generator', icon: 'braces', categories: ['generators'], keywords: ['fake', 'json', 'mock', 'data', 'generate'] },
  { id: 'api-key-generator', name: 'API-Key-like Random String Generator', description: 'Generate an API-key-shaped random string.', route: 'api-key-generator', icon: 'key-round', categories: ['generators'], keywords: ['api key', 'token', 'generate', 'random'] },

  // --- Date & Time ---
  { id: 'timestamp', name: 'Unix Timestamp ↔ Date Converter', description: 'Convert between Unix timestamps and human-readable dates.', route: 'timestamp', icon: 'clock', categories: ['datetime'], keywords: ['unix', 'timestamp', 'epoch', 'date', 'convert'] },
  { id: 'iso8601-formatter', name: 'ISO 8601 Formatter', description: 'Format a date as ISO 8601 in any timezone offset.', route: 'iso8601-formatter', icon: 'calendar-clock', categories: ['datetime'], keywords: ['iso8601', 'iso 8601', 'date', 'format'] },
  { id: 'date-difference', name: 'Date Difference Calculator', description: 'Calculate the difference between two dates.', route: 'date-difference', icon: 'calendar-clock', categories: ['datetime'], keywords: ['date', 'difference', 'calculate', 'duration'] },
  { id: 'cron-generator', name: 'Cron Expression Generator', description: 'Build a cron expression from a schedule.', route: 'cron-generator', icon: 'timer', categories: ['datetime'], keywords: ['cron', 'schedule', 'generate'] },
  { id: 'cron-parser', name: 'Cron Expression Parser / Explainer', description: 'Explain what a cron expression means in plain English.', route: 'cron-parser', icon: 'timer', categories: ['datetime'], keywords: ['cron', 'parse', 'explain'] },
  { id: 'timezone-converter', name: 'Timezone Converter', description: 'Convert a date and time between timezones.', route: 'timezone-converter', icon: 'globe', categories: ['datetime'], keywords: ['timezone', 'convert', 'date', 'time'] },

  // --- Web Development ---
  { id: 'html-formatter', name: 'HTML Formatter', description: 'Format or minify HTML.', route: 'html-formatter', icon: 'code', categories: ['web'], keywords: ['html', 'format', 'minify', 'prettify'] },
  { id: 'css-formatter', name: 'CSS Formatter', description: 'Format or minify CSS.', route: 'css-formatter', icon: 'code', categories: ['web'], keywords: ['css', 'format', 'minify', 'prettify'] },
  { id: 'js-formatter', name: 'JavaScript Formatter', description: 'Format or minify JavaScript.', route: 'js-formatter', icon: 'code', categories: ['web'], keywords: ['javascript', 'js', 'format', 'minify', 'prettify'] },
  { id: 'html-preview', name: 'HTML Preview', description: 'Preview HTML in a sandboxed frame.', route: 'html-preview', icon: 'square-code', categories: ['web'], keywords: ['html', 'preview', 'render'] },
  { id: 'regex-tester', name: 'Regex Tester', description: 'Test a regular expression against sample text and see matches highlighted.', route: 'regex-tester', icon: 'regex', categories: ['web', 'dev-utils'], keywords: ['regex', 'regexp', 'test', 'pattern'] },
  { id: 'regex-generator', name: 'Regex Generator', description: 'Build a regular expression from common patterns.', route: 'regex-generator', icon: 'regex', categories: ['web', 'dev-utils'], keywords: ['regex', 'regexp', 'generate', 'pattern'] },
  { id: 'url-parser', name: 'URL Parser', description: 'Break a URL down into its components.', route: 'url-parser', icon: 'link', categories: ['web'], keywords: ['url', 'parse', 'components'] },
  { id: 'querystring-parser', name: 'Query String Parser / Builder', description: 'Parse a query string into key/value pairs, or build one.', route: 'querystring-parser', icon: 'link', categories: ['web'], keywords: ['query string', 'params', 'parse', 'build'] },
  { id: 'text-case-converter', name: 'Text Case Converter', description: 'Convert text between lowercase, UPPERCASE, camelCase, snake_case, and more.', route: 'text-case-converter', icon: 'case-sensitive', categories: ['web'], keywords: ['case', 'camelcase', 'snake_case', 'kebab-case', 'convert'] },
  { id: 'html-escape', name: 'HTML Escape / Unescape', description: 'Escape or unescape HTML special characters.', route: 'html-escape', icon: 'code', categories: ['web', 'security'], keywords: ['html', 'escape', 'unescape'] },

  // --- SQL Tools ---
  { id: 'sql-formatter', name: 'SQL Formatter', description: 'Format or minify a SQL statement — no database connection.', route: 'sql-formatter', icon: 'database', categories: ['sql'], keywords: ['sql', 'format', 'minify', 'prettify'] },
  { id: 'sql-validator', name: 'SQL Validator', description: 'Check a SQL statement for basic syntax problems.', route: 'sql-validator', icon: 'database', categories: ['sql'], keywords: ['sql', 'validate', 'lint'] },
  { id: 'sql-to-json', name: 'SQL → JSON', description: 'Convert a SQL INSERT statement or result-like table into JSON.', route: 'sql-to-json', icon: 'database', categories: ['sql'], keywords: ['sql', 'json', 'convert'] },

  // --- Developer Utilities ---
  { id: 'diff', name: 'Text Diff / Diff Checker', description: 'Compare two texts side-by-side or as a unified diff.', route: 'diff', icon: 'diff', categories: ['dev-utils'], keywords: ['diff', 'compare', 'text', 'changes'] },
  { id: 'code-beautifier', name: 'Code Beautifier', description: 'Beautify code in several languages.', route: 'code-beautifier', icon: 'wand', categories: ['dev-utils'], keywords: ['beautify', 'format', 'code'] },
  { id: 'code-minifier', name: 'Code Minifier', description: 'Minify JavaScript or CSS.', route: 'code-minifier', icon: 'wand', categories: ['dev-utils'], keywords: ['minify', 'compress', 'code'] },
  { id: 'text-counter', name: 'Line / Word / Character Counter', description: 'Count lines, words, and characters in text.', route: 'text-counter', icon: 'list-ordered', categories: ['dev-utils'], keywords: ['count', 'lines', 'words', 'characters'] },
  { id: 'string-escape', name: 'String Escape / Unescape', description: 'Escape or unescape a string for use as a code literal.', route: 'string-escape', icon: 'code', categories: ['dev-utils'], keywords: ['string', 'escape', 'unescape', 'literal'] },
  { id: 'markdown-preview', name: 'Markdown Preview', description: 'Preview Markdown and view the generated HTML.', route: 'markdown-preview', icon: 'file-type', categories: ['dev-utils'], keywords: ['markdown', 'preview', 'html', 'render'] },

  // --- Network Utilities ---
  { id: 'http-status-lookup', name: 'HTTP Status Code Lookup', description: 'Look up the meaning of an HTTP status code.', route: 'http-status-lookup', icon: 'network', categories: ['network'], keywords: ['http', 'status', 'code', 'lookup'] },
  { id: 'http-header-parser', name: 'HTTP Header Parser', description: 'Parse raw HTTP headers into a readable table.', route: 'http-header-parser', icon: 'network', categories: ['network'], keywords: ['http', 'headers', 'parse'] },
  { id: 'cidr-calculator', name: 'CIDR Calculator', description: 'Calculate network range, mask, and host count from a CIDR block.', route: 'cidr-calculator', icon: 'router', categories: ['network'], keywords: ['cidr', 'subnet', 'ip', 'network'] },
  { id: 'ipv4-ipv6-converter', name: 'IPv4 ↔ IPv6 Converter', description: 'Convert between IPv4 and IPv6 address notation.', route: 'ipv4-ipv6-converter', icon: 'network', categories: ['network'], keywords: ['ipv4', 'ipv6', 'ip address', 'convert'] },
  { id: 'user-agent-parser', name: 'User-Agent Parser', description: 'Parse a User-Agent string into browser, OS, and device.', route: 'user-agent-parser', icon: 'network', categories: ['network'], keywords: ['user agent', 'ua', 'browser', 'parse'] },

  // --- Git Tools ---
  { id: 'git-command-generator', name: 'Git Command Generator', description: 'Build common git commands from a simple form.', route: 'git-command-generator', icon: 'git-branch', categories: ['git'], keywords: ['git', 'command', 'generate'] },
  { id: 'gitignore', name: '.gitignore Generator', description: 'Generate a .gitignore file for your stack.', route: 'gitignore', icon: 'git-branch', categories: ['git'], keywords: ['gitignore', 'git', 'generate'] },
  { id: 'git-diff-viewer', name: 'Git Diff Viewer', description: 'View a git-style unified diff.', route: 'git-diff-viewer', icon: 'diff', categories: ['git'], keywords: ['git', 'diff', 'view'] },
  { id: 'commit-message-generator', name: 'Conventional Git Commit Message Generator', description: 'Build a Conventional Commits message.', route: 'commit-message-generator', icon: 'git-commit', categories: ['git'], keywords: ['git', 'commit', 'conventional commits', 'message'] },

  // --- Code Generators (json-to-typescript reused from JSON Tools) ---
  { id: 'json-to-python', name: 'JSON → Python Model', description: 'Generate a Python dataclass from JSON.', route: 'json-to-python', icon: 'file-code-2', categories: ['code-gen'], keywords: ['json', 'python', 'dataclass', 'codegen'] },
  { id: 'json-to-pydantic', name: 'JSON → Pydantic Model', description: 'Generate a Pydantic model from JSON.', route: 'json-to-pydantic', icon: 'file-code-2', categories: ['code-gen'], keywords: ['json', 'pydantic', 'python', 'codegen'] },
  { id: 'json-to-go', name: 'JSON → Go Struct', description: 'Generate a Go struct from JSON.', route: 'json-to-go', icon: 'file-code-2', categories: ['code-gen'], keywords: ['json', 'go', 'golang', 'struct', 'codegen'] },
  { id: 'json-to-kotlin', name: 'JSON → Kotlin Data Class', description: 'Generate a Kotlin data class from JSON.', route: 'json-to-kotlin', icon: 'file-code-2', categories: ['code-gen'], keywords: ['json', 'kotlin', 'data class', 'codegen'] },
  { id: 'json-to-dart', name: 'JSON → Dart Model', description: 'Generate a Dart model class from JSON.', route: 'json-to-dart', icon: 'file-code-2', categories: ['code-gen'], keywords: ['json', 'dart', 'flutter', 'model', 'codegen'] },

  // --- Security Utilities (hash-generator, jwt-decoder, html-escape reused) ---
  { id: 'password-strength-checker', name: 'Password Strength Checker', description: 'Check password strength locally — never sent or logged.', route: 'password-strength-checker', icon: 'shield-check', categories: ['security'], keywords: ['password', 'strength', 'security', 'check'] },
  { id: 'csp-generator', name: 'CSP Generator', description: 'Build a Content-Security-Policy header value.', route: 'csp-generator', icon: 'shield', categories: ['security'], keywords: ['csp', 'content security policy', 'header', 'security'] },
  { id: 'sri-hash-generator', name: 'SRI Hash Generator', description: 'Generate a Subresource Integrity hash for a local file.', route: 'sri-hash-generator', icon: 'shield-check', categories: ['security'], keywords: ['sri', 'subresource integrity', 'hash', 'security'] },

  // --- Data Conversion (csv-json reused from JSON Tools) ---
  { id: 'csv-yaml', name: 'CSV ↔ YAML', description: 'Convert between CSV and YAML.', route: 'csv-yaml', icon: 'table-properties', categories: ['data-conversion'], keywords: ['csv', 'yaml', 'convert'] },
  { id: 'json-toml', name: 'JSON ↔ TOML', description: 'Convert between JSON and TOML.', route: 'json-toml', icon: 'file-code', categories: ['data-conversion'], keywords: ['json', 'toml', 'convert'] },
  { id: 'number-base-converter', name: 'Number Base Converter', description: 'Convert numbers between binary, octal, decimal, and hexadecimal.', route: 'number-base-converter', icon: 'binary', categories: ['data-conversion'], keywords: ['binary', 'octal', 'decimal', 'hexadecimal', 'base', 'convert'] },
  { id: 'image-base64', name: 'Image ↔ Base64', description: 'Convert an image to Base64, or preview a Base64 string as an image.', route: 'image-base64', icon: 'file-code', categories: ['data-conversion'], keywords: ['image', 'base64', 'convert', 'preview'] },
  { id: 'data-uri-generator', name: 'Data URI Generator', description: 'Generate a data: URI from a local file.', route: 'data-uri-generator', icon: 'link', categories: ['data-conversion'], keywords: ['data uri', 'base64', 'generate'] },
];
