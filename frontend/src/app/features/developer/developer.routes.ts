import { Provider } from '@angular/core';
import { Routes } from '@angular/router';
import { DevFavoritesService } from './shared/dev-favorites.service';
import { DevHistoryService } from './shared/dev-history.service';
import { DEV_TOOLS_STORAGE_SCOPE } from './shared/dev-storage-scope';

/**
 * Developer dashboard + tool routes. Mounted under `/developer` (authenticated shell) and under
 * `/explore/developer` (public guest shell), so links inside the feature must stay relative.
 */
export const DEVELOPER_ROUTES: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./developer-dashboard.component').then(
        (m) => m.DeveloperDashboardComponent,
      ),
  },
  {
    path: 'base64',
    loadComponent: () =>
      import('./tools/encoding/base64.component').then((m) => m.Base64ToolComponent),
  },
  {
    path: 'url-encoder',
    loadComponent: () =>
      import('./tools/encoding/url-encoder.component').then(
        (m) => m.UrlEncoderToolComponent,
      ),
  },
  {
    path: 'html-encoder',
    loadComponent: () =>
      import('./tools/encoding/html-encoder.component').then(
        (m) => m.HtmlEncoderToolComponent,
      ),
  },
  {
    path: 'jwt-decoder',
    loadComponent: () =>
      import('./tools/encoding/jwt-decoder.component').then(
        (m) => m.JwtDecoderToolComponent,
      ),
  },
  {
    path: 'hex-text',
    loadComponent: () =>
      import('./tools/encoding/hex-text.component').then((m) => m.HexTextToolComponent),
  },
  {
    path: 'binary-text',
    loadComponent: () =>
      import('./tools/encoding/binary-text.component').then(
        (m) => m.BinaryTextToolComponent,
      ),
  },
  {
    path: 'ascii-text',
    loadComponent: () =>
      import('./tools/encoding/ascii-text.component').then(
        (m) => m.AsciiTextToolComponent,
      ),
  },
  {
    path: 'unicode-converter',
    loadComponent: () =>
      import('./tools/encoding/unicode-converter.component').then(
        (m) => m.UnicodeConverterToolComponent,
      ),
  },
  {
    path: 'base32',
    loadComponent: () =>
      import('./tools/encoding/base32.component').then((m) => m.Base32ToolComponent),
  },
  {
    path: 'base58',
    loadComponent: () =>
      import('./tools/encoding/base58.component').then((m) => m.Base58ToolComponent),
  },
  {
    path: 'json-formatter',
    loadComponent: () =>
      import('./tools/json/json-formatter.component').then(
        (m) => m.JsonFormatterToolComponent,
      ),
  },
  {
    path: 'json-validator',
    loadComponent: () =>
      import('./tools/json/json-validator.component').then(
        (m) => m.JsonValidatorToolComponent,
      ),
  },
  {
    path: 'json-minifier',
    loadComponent: () =>
      import('./tools/json/json-minifier.component').then(
        (m) => m.JsonMinifierToolComponent,
      ),
  },
  {
    path: 'csv-json',
    loadComponent: () =>
      import('./tools/json/csv-json.component').then((m) => m.CsvJsonToolComponent),
  },
  {
    path: 'json-to-yaml',
    loadComponent: () =>
      import('./tools/json/json-to-yaml.component').then(
        (m) => m.JsonToYamlToolComponent,
      ),
  },
  {
    path: 'json-to-typescript',
    loadComponent: () =>
      import('./tools/json/json-to-typescript.component').then(
        (m) => m.JsonToTypeScriptToolComponent,
      ),
  },
  {
    path: 'jsonpath-tester',
    loadComponent: () =>
      import('./tools/json/jsonpath-tester.component').then(
        (m) => m.JsonpathTesterToolComponent,
      ),
  },
  {
    path: 'json-diff',
    loadComponent: () =>
      import('./tools/json/json-diff.component').then((m) => m.JsonDiffToolComponent),
  },
  {
    path: 'xml-formatter',
    loadComponent: () =>
      import('./tools/xml-yaml/xml-formatter.component').then(
        (m) => m.XmlFormatterToolComponent,
      ),
  },
  {
    path: 'xml-validator',
    loadComponent: () =>
      import('./tools/xml-yaml/xml-validator.component').then(
        (m) => m.XmlValidatorToolComponent,
      ),
  },
  {
    path: 'xml-json',
    loadComponent: () =>
      import('./tools/xml-yaml/xml-json.component').then((m) => m.XmlJsonToolComponent),
  },
  {
    path: 'yaml-formatter',
    loadComponent: () =>
      import('./tools/xml-yaml/yaml-formatter.component').then(
        (m) => m.YamlFormatterToolComponent,
      ),
  },
  {
    path: 'yaml-json',
    loadComponent: () =>
      import('./tools/xml-yaml/yaml-json.component').then((m) => m.YamlJsonToolComponent),
  },
  {
    path: 'hash-generator',
    loadComponent: () =>
      import('./tools/hashing/hash-generator.component').then(
        (m) => m.HashGeneratorToolComponent,
      ),
  },
  {
    path: 'hmac-generator',
    loadComponent: () =>
      import('./tools/hashing/hmac-generator.component').then(
        (m) => m.HmacGeneratorToolComponent,
      ),
  },
  {
    path: 'uuid-generator',
    loadComponent: () =>
      import('./tools/generators/uuid-generator.component').then(
        (m) => m.UuidGeneratorToolComponent,
      ),
  },
  {
    path: 'random-string-generator',
    loadComponent: () =>
      import('./tools/generators/random-string-generator.component').then(
        (m) => m.RandomStringGeneratorToolComponent,
      ),
  },
  {
    path: 'password-generator',
    loadComponent: () =>
      import('./tools/generators/password-generator.component').then(
        (m) => m.PasswordGeneratorToolComponent,
      ),
  },
  {
    path: 'lorem-ipsum-generator',
    loadComponent: () =>
      import('./tools/generators/lorem-ipsum-generator.component').then(
        (m) => m.LoremIpsumGeneratorToolComponent,
      ),
  },
  {
    path: 'fake-json-generator',
    loadComponent: () =>
      import('./tools/generators/fake-json-generator.component').then(
        (m) => m.FakeJsonGeneratorToolComponent,
      ),
  },
  {
    path: 'api-key-generator',
    loadComponent: () =>
      import('./tools/generators/api-key-generator.component').then(
        (m) => m.ApiKeyGeneratorToolComponent,
      ),
  },
  {
    path: 'timestamp',
    loadComponent: () =>
      import('./tools/datetime/timestamp.component').then(
        (m) => m.TimestampToolComponent,
      ),
  },
  {
    path: 'iso8601-formatter',
    loadComponent: () =>
      import('./tools/datetime/iso8601-formatter.component').then(
        (m) => m.Iso8601FormatterToolComponent,
      ),
  },
  {
    path: 'date-difference',
    loadComponent: () =>
      import('./tools/datetime/date-difference.component').then(
        (m) => m.DateDifferenceToolComponent,
      ),
  },
  {
    path: 'cron-generator',
    loadComponent: () =>
      import('./tools/datetime/cron-generator.component').then(
        (m) => m.CronGeneratorToolComponent,
      ),
  },
  {
    path: 'cron-parser',
    loadComponent: () =>
      import('./tools/datetime/cron-parser.component').then(
        (m) => m.CronParserToolComponent,
      ),
  },
  {
    path: 'timezone-converter',
    loadComponent: () =>
      import('./tools/datetime/timezone-converter.component').then(
        (m) => m.TimezoneConverterToolComponent,
      ),
  },
  {
    path: 'html-formatter',
    loadComponent: () =>
      import('./tools/web/html-formatter.component').then(
        (m) => m.HtmlFormatterToolComponent,
      ),
  },
  {
    path: 'css-formatter',
    loadComponent: () =>
      import('./tools/web/css-formatter.component').then(
        (m) => m.CssFormatterToolComponent,
      ),
  },
  {
    path: 'js-formatter',
    loadComponent: () =>
      import('./tools/web/js-formatter.component').then((m) => m.JsFormatterToolComponent),
  },
  {
    path: 'html-preview',
    loadComponent: () =>
      import('./tools/web/html-preview.component').then(
        (m) => m.HtmlPreviewToolComponent,
      ),
  },
  {
    path: 'regex-tester',
    loadComponent: () =>
      import('./tools/web/regex-tester.component').then(
        (m) => m.RegexTesterToolComponent,
      ),
  },
  {
    path: 'regex-generator',
    loadComponent: () =>
      import('./tools/web/regex-generator.component').then(
        (m) => m.RegexGeneratorToolComponent,
      ),
  },
  {
    path: 'url-parser',
    loadComponent: () =>
      import('./tools/web/url-parser.component').then((m) => m.UrlParserToolComponent),
  },
  {
    path: 'querystring-parser',
    loadComponent: () =>
      import('./tools/web/querystring-parser.component').then(
        (m) => m.QuerystringParserToolComponent,
      ),
  },
  {
    path: 'text-case-converter',
    loadComponent: () =>
      import('./tools/web/text-case-converter.component').then(
        (m) => m.TextCaseConverterToolComponent,
      ),
  },
  {
    path: 'html-escape',
    loadComponent: () =>
      import('./tools/web/html-escape.component').then(
        (m) => m.HtmlEscapeToolComponent,
      ),
  },
  {
    path: 'sql-formatter',
    loadComponent: () =>
      import('./tools/sql/sql-formatter.component').then(
        (m) => m.SqlFormatterToolComponent,
      ),
  },
  {
    path: 'sql-validator',
    loadComponent: () =>
      import('./tools/sql/sql-validator.component').then(
        (m) => m.SqlValidatorToolComponent,
      ),
  },
  {
    path: 'sql-to-json',
    loadComponent: () =>
      import('./tools/sql/sql-to-json.component').then(
        (m) => m.SqlToJsonToolComponent,
      ),
  },
  {
    path: 'diff',
    loadComponent: () =>
      import('./tools/dev-utils/diff.component').then((m) => m.DiffToolComponent),
  },
  {
    path: 'code-beautifier',
    loadComponent: () =>
      import('./tools/dev-utils/code-beautifier.component').then(
        (m) => m.CodeBeautifierToolComponent,
      ),
  },
  {
    path: 'code-minifier',
    loadComponent: () =>
      import('./tools/dev-utils/code-minifier.component').then(
        (m) => m.CodeMinifierToolComponent,
      ),
  },
  {
    path: 'text-counter',
    loadComponent: () =>
      import('./tools/dev-utils/text-counter.component').then(
        (m) => m.TextCounterToolComponent,
      ),
  },
  {
    path: 'string-escape',
    loadComponent: () =>
      import('./tools/dev-utils/string-escape.component').then(
        (m) => m.StringEscapeToolComponent,
      ),
  },
  {
    path: 'markdown-preview',
    loadComponent: () =>
      import('./tools/dev-utils/markdown-preview.component').then(
        (m) => m.MarkdownPreviewToolComponent,
      ),
  },
  {
    path: 'http-status-lookup',
    loadComponent: () =>
      import('./tools/network/http-status-lookup.component').then(
        (m) => m.HttpStatusLookupToolComponent,
      ),
  },
  {
    path: 'http-header-parser',
    loadComponent: () =>
      import('./tools/network/http-header-parser.component').then(
        (m) => m.HttpHeaderParserToolComponent,
      ),
  },
  {
    path: 'cidr-calculator',
    loadComponent: () =>
      import('./tools/network/cidr-calculator.component').then(
        (m) => m.CidrCalculatorToolComponent,
      ),
  },
  {
    path: 'ipv4-ipv6-converter',
    loadComponent: () =>
      import('./tools/network/ipv4-ipv6-converter.component').then(
        (m) => m.Ipv4Ipv6ConverterToolComponent,
      ),
  },
  {
    path: 'user-agent-parser',
    loadComponent: () =>
      import('./tools/network/user-agent-parser.component').then(
        (m) => m.UserAgentParserToolComponent,
      ),
  },
  {
    path: 'git-command-generator',
    loadComponent: () =>
      import('./tools/git/git-command-generator.component').then(
        (m) => m.GitCommandGeneratorToolComponent,
      ),
  },
  {
    path: 'gitignore',
    loadComponent: () =>
      import('./tools/git/gitignore.component').then((m) => m.GitignoreToolComponent),
  },
  {
    path: 'git-diff-viewer',
    loadComponent: () =>
      import('./tools/git/git-diff-viewer.component').then(
        (m) => m.GitDiffViewerToolComponent,
      ),
  },
  {
    path: 'commit-message-generator',
    loadComponent: () =>
      import('./tools/git/commit-message-generator.component').then(
        (m) => m.CommitMessageGeneratorToolComponent,
      ),
  },
  {
    path: 'json-to-python',
    loadComponent: () =>
      import('./tools/codegen/json-to-python.component').then(
        (m) => m.JsonToPythonToolComponent,
      ),
  },
  {
    path: 'json-to-pydantic',
    loadComponent: () =>
      import('./tools/codegen/json-to-pydantic.component').then(
        (m) => m.JsonToPydanticToolComponent,
      ),
  },
  {
    path: 'json-to-go',
    loadComponent: () =>
      import('./tools/codegen/json-to-go.component').then(
        (m) => m.JsonToGoToolComponent,
      ),
  },
  {
    path: 'json-to-kotlin',
    loadComponent: () =>
      import('./tools/codegen/json-to-kotlin.component').then(
        (m) => m.JsonToKotlinToolComponent,
      ),
  },
  {
    path: 'json-to-dart',
    loadComponent: () =>
      import('./tools/codegen/json-to-dart.component').then(
        (m) => m.JsonToDartToolComponent,
      ),
  },
  {
    path: 'password-strength-checker',
    loadComponent: () =>
      import('./tools/security/password-strength-checker.component').then(
        (m) => m.PasswordStrengthCheckerToolComponent,
      ),
  },
  {
    path: 'csp-generator',
    loadComponent: () =>
      import('./tools/security/csp-generator.component').then(
        (m) => m.CspGeneratorToolComponent,
      ),
  },
  {
    path: 'sri-hash-generator',
    loadComponent: () =>
      import('./tools/security/sri-hash-generator.component').then(
        (m) => m.SriHashGeneratorToolComponent,
      ),
  },
  {
    path: 'csv-yaml',
    loadComponent: () =>
      import('./tools/data-conversion/csv-yaml.component').then(
        (m) => m.CsvYamlToolComponent,
      ),
  },
  {
    path: 'json-toml',
    loadComponent: () =>
      import('./tools/data-conversion/json-toml.component').then(
        (m) => m.JsonTomlToolComponent,
      ),
  },
  {
    path: 'number-base-converter',
    loadComponent: () =>
      import('./tools/data-conversion/number-base-converter.component').then(
        (m) => m.NumberBaseConverterToolComponent,
      ),
  },
  {
    path: 'image-base64',
    loadComponent: () =>
      import('./tools/data-conversion/image-base64.component').then(
        (m) => m.ImageBase64ToolComponent,
      ),
  },
  {
    path: 'data-uri-generator',
    loadComponent: () =>
      import('./tools/data-conversion/data-uri-generator.component').then(
        (m) => m.DataUriGeneratorToolComponent,
      ),
  },
];

/** Route-level providers for the guest mount: separate favorites/history storage from the owner's. */
export const DEVELOPER_GUEST_PROVIDERS: Provider[] = [
  { provide: DEV_TOOLS_STORAGE_SCOPE, useValue: 'guest' },
  DevFavoritesService,
  DevHistoryService,
];
