import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';
import { registrationUnlockGuard } from './core/guards/registration-unlock.guard';

export const routes: Routes = [
  {
    path: 'offline',
    loadComponent: () =>
      import('./features/offline/offline-page.component').then((m) => m.OfflinePageComponent),
  },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login.component').then((m) => m.LoginComponent),
    canActivate: [guestGuard],
  },
  {
    path: 'register-access',
    loadComponent: () =>
      import('./features/auth/registration-gate.component').then((m) => m.RegistrationGateComponent),
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register.component').then((m) => m.RegisterComponent),
    canActivate: [guestGuard, registrationUnlockGuard],
  },
  {
    path: 'add-new-user',
    loadComponent: () =>
      import('./features/auth/add-new-user.component').then((m) => m.AddNewUserComponent),
    canActivate: [registrationUnlockGuard],
  },
  {
    path: '',
    loadComponent: () =>
      import('./shared/layout/app-shell.component').then((m) => m.AppShellComponent),
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'analytics/dashboard' },
      {
        path: 'quick-action',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      { path: 'dashboard', pathMatch: 'full', redirectTo: 'quick-action' },
      {
        path: 'profile',
        loadComponent: () =>
          import('./features/settings/settings-fragment-redirect.component').then(
            (m) => m.SettingsFragmentRedirectComponent,
          ),
        data: { fragment: 'profile' },
      },
      {
        path: 'password',
        loadComponent: () =>
          import('./features/settings/settings-fragment-redirect.component').then(
            (m) => m.SettingsFragmentRedirectComponent,
          ),
        data: { fragment: 'password' },
      },
      {
        path: 'sidebar',
        loadComponent: () =>
          import('./features/settings/settings-fragment-redirect.component').then(
            (m) => m.SettingsFragmentRedirectComponent,
          ),
        data: { fragment: 'sidebar' },
      },
      {
        path: 'goals',
        loadComponent: () =>
          import('./features/goals/goals-list.component').then((m) => m.GoalsListComponent),
      },
      {
        path: 'goals/new',
        loadComponent: () =>
          import('./features/goals/goal-form.component').then((m) => m.GoalFormComponent),
      },
      {
        path: 'goals/:id/edit',
        loadComponent: () =>
          import('./features/goals/goal-form.component').then((m) => m.GoalFormComponent),
      },
      {
        path: 'goals/:id',
        loadComponent: () =>
          import('./features/goals/goal-detail.component').then((m) => m.GoalDetailComponent),
      },
      {
        path: 'tasks',
        loadComponent: () =>
          import('./features/tasks/tasks-list.component').then((m) => m.TasksListComponent),
      },
      {
        path: 'tasks/new',
        loadComponent: () =>
          import('./features/tasks/task-form.component').then((m) => m.TaskFormComponent),
      },
      {
        path: 'tasks/:id/edit',
        loadComponent: () =>
          import('./features/tasks/task-form.component').then((m) => m.TaskFormComponent),
      },
      {
        path: 'tasks/:id',
        loadComponent: () =>
          import('./features/tasks/task-detail.component').then((m) => m.TaskDetailComponent),
      },
      {
        path: 'habits',
        loadComponent: () =>
          import('./features/habits/habits-list.component').then((m) => m.HabitsListComponent),
      },
      {
        path: 'habits/new',
        loadComponent: () =>
          import('./features/habits/habit-form.component').then((m) => m.HabitFormComponent),
      },
      {
        path: 'habits/:id/edit',
        loadComponent: () =>
          import('./features/habits/habit-form.component').then((m) => m.HabitFormComponent),
      },
      {
        path: 'habits/:id',
        loadComponent: () =>
          import('./features/habits/habit-detail.component').then((m) => m.HabitDetailComponent),
      },
      {
        path: 'running/new',
        loadComponent: () =>
          import('./features/running/run-form.component').then((m) => m.RunFormComponent),
      },
      {
        path: 'running/races/new',
        loadComponent: () =>
          import('./features/running/race-event-form.component').then((m) => m.RaceEventFormComponent),
      },
      {
        path: 'running/races/:id/edit',
        loadComponent: () =>
          import('./features/running/race-event-form.component').then((m) => m.RaceEventFormComponent),
      },
      {
        path: 'running/races/:id',
        loadComponent: () =>
          import('./features/running/race-event-detail.component').then((m) => m.RaceEventDetailComponent),
      },
      {
        path: 'running/:id/edit',
        loadComponent: () =>
          import('./features/running/run-form.component').then((m) => m.RunFormComponent),
      },
      {
        path: 'running/:id',
        loadComponent: () =>
          import('./features/running/run-detail.component').then((m) => m.RunDetailComponent),
      },
      {
        path: 'running',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/running/running-list.component').then((m) => m.RunningListComponent),
      },
      {
        path: 'calendar',
        loadComponent: () =>
          import('./features/calendar/calendar-list.component').then((m) => m.CalendarListComponent),
      },
      {
        path: 'calendar/new',
        loadComponent: () =>
          import('./features/calendar/event-form.component').then((m) => m.EventFormComponent),
      },
      {
        path: 'calendar/:id/edit',
        loadComponent: () =>
          import('./features/calendar/event-form.component').then((m) => m.EventFormComponent),
      },
      {
        path: 'calendar/:id',
        loadComponent: () =>
          import('./features/calendar/event-detail.component').then((m) => m.EventDetailComponent),
      },
      {
        path: 'routines',
        loadComponent: () =>
          import('./features/routines/routines-list.component').then((m) => m.RoutinesListComponent),
      },
      {
        path: 'routines/new',
        loadComponent: () =>
          import('./features/routines/routine-form.component').then((m) => m.RoutineFormComponent),
      },
      {
        path: 'routines/:id/edit',
        loadComponent: () =>
          import('./features/routines/routine-form.component').then((m) => m.RoutineFormComponent),
      },
      {
        path: 'routines/:id',
        loadComponent: () =>
          import('./features/routines/routine-detail.component').then((m) => m.RoutineDetailComponent),
      },
      {
        path: 'journal',
        loadComponent: () =>
          import('./features/journal/journal-list.component').then((m) => m.JournalListComponent),
      },
      {
        path: 'journal/new',
        loadComponent: () =>
          import('./features/journal/journal-form.component').then((m) => m.JournalFormComponent),
      },
      {
        path: 'journal/:id/edit',
        loadComponent: () =>
          import('./features/journal/journal-form.component').then((m) => m.JournalFormComponent),
      },
      {
        path: 'journal/:id',
        loadComponent: () =>
          import('./features/journal/journal-detail.component').then((m) => m.JournalDetailComponent),
      },
      {
        path: 'mood',
        loadComponent: () =>
          import('./features/mood/mood-page.component').then((m) => m.MoodPageComponent),
      },
      {
        path: 'communication',
        loadComponent: () =>
          import('./features/communication/communication-hub.component').then((m) => m.CommunicationHubComponent),
      },
      {
        path: 'communication/vocabulary/:id',
        loadComponent: () =>
          import('./features/communication/vocabulary/vocabulary-detail.component').then(
            (m) => m.VocabularyDetailComponent,
          ),
      },
      {
        path: 'communication/writing/new',
        loadComponent: () =>
          import('./features/communication/writing-form.component').then((m) => m.WritingFormComponent),
      },
      {
        path: 'communication/writing/:id/edit',
        loadComponent: () =>
          import('./features/communication/writing-form.component').then((m) => m.WritingFormComponent),
      },
      {
        path: 'communication/writing/:id',
        loadComponent: () =>
          import('./features/communication/writing-detail.component').then((m) => m.WritingDetailComponent),
      },
      {
        path: 'communication/speaking/new',
        loadComponent: () =>
          import('./features/communication/speaking-form.component').then((m) => m.SpeakingFormComponent),
      },
      {
        path: 'communication/speaking/:id/edit',
        loadComponent: () =>
          import('./features/communication/speaking-form.component').then((m) => m.SpeakingFormComponent),
      },
      {
        path: 'communication/speaking/:id',
        loadComponent: () =>
          import('./features/communication/speaking-detail.component').then((m) => m.SpeakingDetailComponent),
      },
      {
        path: 'qa',
        loadComponent: () => import('./features/qa/qa-list.component').then((m) => m.QAListComponent),
      },
      {
        path: 'qa/new',
        loadComponent: () => import('./features/qa/qa-form.component').then((m) => m.QAFormComponent),
      },
      {
        path: 'qa/:id/edit',
        loadComponent: () => import('./features/qa/qa-form.component').then((m) => m.QAFormComponent),
      },
      {
        path: 'qa/:id',
        loadComponent: () => import('./features/qa/qa-detail.component').then((m) => m.QADetailComponent),
      },
      {
        path: 'knowledge',
        loadComponent: () =>
          import('./features/knowledge-notes/knowledge-notes-list.component').then(
            (m) => m.KnowledgeNotesListComponent,
          ),
      },
      {
        path: 'knowledge/:id',
        loadComponent: () =>
          import('./features/knowledge-notes/knowledge-subject.component').then(
            (m) => m.KnowledgeSubjectComponent,
          ),
      },
      {
        path: 'wishlist',
        loadComponent: () =>
          import('./features/wishlist/wishlist-list.component').then((m) => m.WishlistListComponent),
      },
      {
        path: 'wishlist/new',
        loadComponent: () =>
          import('./features/wishlist/wishlist-form.component').then((m) => m.WishlistFormComponent),
      },
      {
        path: 'wishlist/:id/edit',
        loadComponent: () =>
          import('./features/wishlist/wishlist-form.component').then((m) => m.WishlistFormComponent),
      },
      {
        path: 'wishlist/:id',
        loadComponent: () =>
          import('./features/wishlist/wishlist-detail.component').then((m) => m.WishlistDetailComponent),
      },
      {
        path: 'search',
        loadComponent: () =>
          import('./features/search/search-page.component').then((m) => m.SearchPageComponent),
      },
      {
        path: 'developer',
        pathMatch: 'full',
        loadComponent: () =>
          import('./features/developer/developer-dashboard.component').then(
            (m) => m.DeveloperDashboardComponent,
          ),
      },
      {
        path: 'developer/base64',
        loadComponent: () =>
          import('./features/developer/tools/encoding/base64.component').then((m) => m.Base64ToolComponent),
      },
      {
        path: 'developer/url-encoder',
        loadComponent: () =>
          import('./features/developer/tools/encoding/url-encoder.component').then(
            (m) => m.UrlEncoderToolComponent,
          ),
      },
      {
        path: 'developer/html-encoder',
        loadComponent: () =>
          import('./features/developer/tools/encoding/html-encoder.component').then(
            (m) => m.HtmlEncoderToolComponent,
          ),
      },
      {
        path: 'developer/jwt-decoder',
        loadComponent: () =>
          import('./features/developer/tools/encoding/jwt-decoder.component').then(
            (m) => m.JwtDecoderToolComponent,
          ),
      },
      {
        path: 'developer/hex-text',
        loadComponent: () =>
          import('./features/developer/tools/encoding/hex-text.component').then((m) => m.HexTextToolComponent),
      },
      {
        path: 'developer/binary-text',
        loadComponent: () =>
          import('./features/developer/tools/encoding/binary-text.component').then(
            (m) => m.BinaryTextToolComponent,
          ),
      },
      {
        path: 'developer/ascii-text',
        loadComponent: () =>
          import('./features/developer/tools/encoding/ascii-text.component').then(
            (m) => m.AsciiTextToolComponent,
          ),
      },
      {
        path: 'developer/unicode-converter',
        loadComponent: () =>
          import('./features/developer/tools/encoding/unicode-converter.component').then(
            (m) => m.UnicodeConverterToolComponent,
          ),
      },
      {
        path: 'developer/base32',
        loadComponent: () =>
          import('./features/developer/tools/encoding/base32.component').then((m) => m.Base32ToolComponent),
      },
      {
        path: 'developer/base58',
        loadComponent: () =>
          import('./features/developer/tools/encoding/base58.component').then((m) => m.Base58ToolComponent),
      },
      {
        path: 'developer/json-formatter',
        loadComponent: () =>
          import('./features/developer/tools/json/json-formatter.component').then(
            (m) => m.JsonFormatterToolComponent,
          ),
      },
      {
        path: 'developer/json-validator',
        loadComponent: () =>
          import('./features/developer/tools/json/json-validator.component').then(
            (m) => m.JsonValidatorToolComponent,
          ),
      },
      {
        path: 'developer/json-minifier',
        loadComponent: () =>
          import('./features/developer/tools/json/json-minifier.component').then(
            (m) => m.JsonMinifierToolComponent,
          ),
      },
      {
        path: 'developer/csv-json',
        loadComponent: () =>
          import('./features/developer/tools/json/csv-json.component').then((m) => m.CsvJsonToolComponent),
      },
      {
        path: 'developer/json-to-yaml',
        loadComponent: () =>
          import('./features/developer/tools/json/json-to-yaml.component').then(
            (m) => m.JsonToYamlToolComponent,
          ),
      },
      {
        path: 'developer/json-to-typescript',
        loadComponent: () =>
          import('./features/developer/tools/json/json-to-typescript.component').then(
            (m) => m.JsonToTypeScriptToolComponent,
          ),
      },
      {
        path: 'developer/jsonpath-tester',
        loadComponent: () =>
          import('./features/developer/tools/json/jsonpath-tester.component').then(
            (m) => m.JsonpathTesterToolComponent,
          ),
      },
      {
        path: 'developer/json-diff',
        loadComponent: () =>
          import('./features/developer/tools/json/json-diff.component').then((m) => m.JsonDiffToolComponent),
      },
      {
        path: 'developer/xml-formatter',
        loadComponent: () =>
          import('./features/developer/tools/xml-yaml/xml-formatter.component').then(
            (m) => m.XmlFormatterToolComponent,
          ),
      },
      {
        path: 'developer/xml-validator',
        loadComponent: () =>
          import('./features/developer/tools/xml-yaml/xml-validator.component').then(
            (m) => m.XmlValidatorToolComponent,
          ),
      },
      {
        path: 'developer/xml-json',
        loadComponent: () =>
          import('./features/developer/tools/xml-yaml/xml-json.component').then((m) => m.XmlJsonToolComponent),
      },
      {
        path: 'developer/yaml-formatter',
        loadComponent: () =>
          import('./features/developer/tools/xml-yaml/yaml-formatter.component').then(
            (m) => m.YamlFormatterToolComponent,
          ),
      },
      {
        path: 'developer/yaml-json',
        loadComponent: () =>
          import('./features/developer/tools/xml-yaml/yaml-json.component').then((m) => m.YamlJsonToolComponent),
      },
      {
        path: 'developer/hash-generator',
        loadComponent: () =>
          import('./features/developer/tools/hashing/hash-generator.component').then(
            (m) => m.HashGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/hmac-generator',
        loadComponent: () =>
          import('./features/developer/tools/hashing/hmac-generator.component').then(
            (m) => m.HmacGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/uuid-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/uuid-generator.component').then(
            (m) => m.UuidGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/random-string-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/random-string-generator.component').then(
            (m) => m.RandomStringGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/password-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/password-generator.component').then(
            (m) => m.PasswordGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/lorem-ipsum-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/lorem-ipsum-generator.component').then(
            (m) => m.LoremIpsumGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/fake-json-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/fake-json-generator.component').then(
            (m) => m.FakeJsonGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/api-key-generator',
        loadComponent: () =>
          import('./features/developer/tools/generators/api-key-generator.component').then(
            (m) => m.ApiKeyGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/timestamp',
        loadComponent: () =>
          import('./features/developer/tools/datetime/timestamp.component').then(
            (m) => m.TimestampToolComponent,
          ),
      },
      {
        path: 'developer/iso8601-formatter',
        loadComponent: () =>
          import('./features/developer/tools/datetime/iso8601-formatter.component').then(
            (m) => m.Iso8601FormatterToolComponent,
          ),
      },
      {
        path: 'developer/date-difference',
        loadComponent: () =>
          import('./features/developer/tools/datetime/date-difference.component').then(
            (m) => m.DateDifferenceToolComponent,
          ),
      },
      {
        path: 'developer/cron-generator',
        loadComponent: () =>
          import('./features/developer/tools/datetime/cron-generator.component').then(
            (m) => m.CronGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/cron-parser',
        loadComponent: () =>
          import('./features/developer/tools/datetime/cron-parser.component').then(
            (m) => m.CronParserToolComponent,
          ),
      },
      {
        path: 'developer/timezone-converter',
        loadComponent: () =>
          import('./features/developer/tools/datetime/timezone-converter.component').then(
            (m) => m.TimezoneConverterToolComponent,
          ),
      },
      {
        path: 'developer/html-formatter',
        loadComponent: () =>
          import('./features/developer/tools/web/html-formatter.component').then(
            (m) => m.HtmlFormatterToolComponent,
          ),
      },
      {
        path: 'developer/css-formatter',
        loadComponent: () =>
          import('./features/developer/tools/web/css-formatter.component').then(
            (m) => m.CssFormatterToolComponent,
          ),
      },
      {
        path: 'developer/js-formatter',
        loadComponent: () =>
          import('./features/developer/tools/web/js-formatter.component').then((m) => m.JsFormatterToolComponent),
      },
      {
        path: 'developer/html-preview',
        loadComponent: () =>
          import('./features/developer/tools/web/html-preview.component').then(
            (m) => m.HtmlPreviewToolComponent,
          ),
      },
      {
        path: 'developer/regex-tester',
        loadComponent: () =>
          import('./features/developer/tools/web/regex-tester.component').then(
            (m) => m.RegexTesterToolComponent,
          ),
      },
      {
        path: 'developer/regex-generator',
        loadComponent: () =>
          import('./features/developer/tools/web/regex-generator.component').then(
            (m) => m.RegexGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/url-parser',
        loadComponent: () =>
          import('./features/developer/tools/web/url-parser.component').then((m) => m.UrlParserToolComponent),
      },
      {
        path: 'developer/querystring-parser',
        loadComponent: () =>
          import('./features/developer/tools/web/querystring-parser.component').then(
            (m) => m.QuerystringParserToolComponent,
          ),
      },
      {
        path: 'developer/text-case-converter',
        loadComponent: () =>
          import('./features/developer/tools/web/text-case-converter.component').then(
            (m) => m.TextCaseConverterToolComponent,
          ),
      },
      {
        path: 'developer/html-escape',
        loadComponent: () =>
          import('./features/developer/tools/web/html-escape.component').then(
            (m) => m.HtmlEscapeToolComponent,
          ),
      },
      {
        path: 'developer/sql-formatter',
        loadComponent: () =>
          import('./features/developer/tools/sql/sql-formatter.component').then(
            (m) => m.SqlFormatterToolComponent,
          ),
      },
      {
        path: 'developer/sql-validator',
        loadComponent: () =>
          import('./features/developer/tools/sql/sql-validator.component').then(
            (m) => m.SqlValidatorToolComponent,
          ),
      },
      {
        path: 'developer/sql-to-json',
        loadComponent: () =>
          import('./features/developer/tools/sql/sql-to-json.component').then(
            (m) => m.SqlToJsonToolComponent,
          ),
      },
      {
        path: 'developer/diff',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/diff.component').then((m) => m.DiffToolComponent),
      },
      {
        path: 'developer/code-beautifier',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/code-beautifier.component').then(
            (m) => m.CodeBeautifierToolComponent,
          ),
      },
      {
        path: 'developer/code-minifier',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/code-minifier.component').then(
            (m) => m.CodeMinifierToolComponent,
          ),
      },
      {
        path: 'developer/text-counter',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/text-counter.component').then(
            (m) => m.TextCounterToolComponent,
          ),
      },
      {
        path: 'developer/string-escape',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/string-escape.component').then(
            (m) => m.StringEscapeToolComponent,
          ),
      },
      {
        path: 'developer/markdown-preview',
        loadComponent: () =>
          import('./features/developer/tools/dev-utils/markdown-preview.component').then(
            (m) => m.MarkdownPreviewToolComponent,
          ),
      },
      {
        path: 'developer/http-status-lookup',
        loadComponent: () =>
          import('./features/developer/tools/network/http-status-lookup.component').then(
            (m) => m.HttpStatusLookupToolComponent,
          ),
      },
      {
        path: 'developer/http-header-parser',
        loadComponent: () =>
          import('./features/developer/tools/network/http-header-parser.component').then(
            (m) => m.HttpHeaderParserToolComponent,
          ),
      },
      {
        path: 'developer/cidr-calculator',
        loadComponent: () =>
          import('./features/developer/tools/network/cidr-calculator.component').then(
            (m) => m.CidrCalculatorToolComponent,
          ),
      },
      {
        path: 'developer/ipv4-ipv6-converter',
        loadComponent: () =>
          import('./features/developer/tools/network/ipv4-ipv6-converter.component').then(
            (m) => m.Ipv4Ipv6ConverterToolComponent,
          ),
      },
      {
        path: 'developer/user-agent-parser',
        loadComponent: () =>
          import('./features/developer/tools/network/user-agent-parser.component').then(
            (m) => m.UserAgentParserToolComponent,
          ),
      },
      {
        path: 'developer/git-command-generator',
        loadComponent: () =>
          import('./features/developer/tools/git/git-command-generator.component').then(
            (m) => m.GitCommandGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/gitignore',
        loadComponent: () =>
          import('./features/developer/tools/git/gitignore.component').then((m) => m.GitignoreToolComponent),
      },
      {
        path: 'developer/git-diff-viewer',
        loadComponent: () =>
          import('./features/developer/tools/git/git-diff-viewer.component').then(
            (m) => m.GitDiffViewerToolComponent,
          ),
      },
      {
        path: 'developer/commit-message-generator',
        loadComponent: () =>
          import('./features/developer/tools/git/commit-message-generator.component').then(
            (m) => m.CommitMessageGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/json-to-python',
        loadComponent: () =>
          import('./features/developer/tools/codegen/json-to-python.component').then(
            (m) => m.JsonToPythonToolComponent,
          ),
      },
      {
        path: 'developer/json-to-pydantic',
        loadComponent: () =>
          import('./features/developer/tools/codegen/json-to-pydantic.component').then(
            (m) => m.JsonToPydanticToolComponent,
          ),
      },
      {
        path: 'developer/json-to-go',
        loadComponent: () =>
          import('./features/developer/tools/codegen/json-to-go.component').then(
            (m) => m.JsonToGoToolComponent,
          ),
      },
      {
        path: 'developer/json-to-kotlin',
        loadComponent: () =>
          import('./features/developer/tools/codegen/json-to-kotlin.component').then(
            (m) => m.JsonToKotlinToolComponent,
          ),
      },
      {
        path: 'developer/json-to-dart',
        loadComponent: () =>
          import('./features/developer/tools/codegen/json-to-dart.component').then(
            (m) => m.JsonToDartToolComponent,
          ),
      },
      {
        path: 'developer/password-strength-checker',
        loadComponent: () =>
          import('./features/developer/tools/security/password-strength-checker.component').then(
            (m) => m.PasswordStrengthCheckerToolComponent,
          ),
      },
      {
        path: 'developer/csp-generator',
        loadComponent: () =>
          import('./features/developer/tools/security/csp-generator.component').then(
            (m) => m.CspGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/sri-hash-generator',
        loadComponent: () =>
          import('./features/developer/tools/security/sri-hash-generator.component').then(
            (m) => m.SriHashGeneratorToolComponent,
          ),
      },
      {
        path: 'developer/csv-yaml',
        loadComponent: () =>
          import('./features/developer/tools/data-conversion/csv-yaml.component').then(
            (m) => m.CsvYamlToolComponent,
          ),
      },
      {
        path: 'developer/json-toml',
        loadComponent: () =>
          import('./features/developer/tools/data-conversion/json-toml.component').then(
            (m) => m.JsonTomlToolComponent,
          ),
      },
      {
        path: 'developer/number-base-converter',
        loadComponent: () =>
          import('./features/developer/tools/data-conversion/number-base-converter.component').then(
            (m) => m.NumberBaseConverterToolComponent,
          ),
      },
      {
        path: 'developer/image-base64',
        loadComponent: () =>
          import('./features/developer/tools/data-conversion/image-base64.component').then(
            (m) => m.ImageBase64ToolComponent,
          ),
      },
      {
        path: 'developer/data-uri-generator',
        loadComponent: () =>
          import('./features/developer/tools/data-conversion/data-uri-generator.component').then(
            (m) => m.DataUriGeneratorToolComponent,
          ),
      },
      {
        path: 'notifications',
        loadComponent: () =>
          import('./features/notifications/notifications-page.component').then(
            (m) => m.NotificationsPageComponent,
          ),
      },
      {
        path: 'export',
        loadComponent: () =>
          import('./features/settings/settings-fragment-redirect.component').then(
            (m) => m.SettingsFragmentRedirectComponent,
          ),
        data: { fragment: 'export' },
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/settings-hub.component').then((m) => m.SettingsHubComponent),
      },
      {
        path: 'assistant',
        loadComponent: () =>
          import('./features/assistant/assistant-page.component').then((m) => m.AssistantPageComponent),
      },
      {
        path: 'files',
        redirectTo: 'documents?tab=library',
        pathMatch: 'full',
      },
      {
        path: 'documents',
        loadComponent: () =>
          import('./features/documents/documents-hub.component').then((m) => m.DocumentsHubComponent),
      },
      {
        path: 'learning',
        loadComponent: () =>
          import('./features/learning/learning-page.component').then((m) => m.LearningListComponent),
      },
      {
        path: 'learning/tracks',
        loadComponent: () =>
          import('./features/learning/track-views.component').then((m) => m.LearningTracksComponent),
      },
      {
        path: 'learning/tracks/:id',
        loadComponent: () =>
          import('./features/learning/track-views.component').then((m) => m.LearningTrackDetailComponent),
      },
      {
        path: 'learning/today',
        loadComponent: () =>
          import('./features/learning/today-view.component').then((m) => m.LearningTodayComponent),
      },
      {
        path: 'learning/concepts/:id',
        loadComponent: () =>
          import('./features/learning/concept-detail.component').then((m) => m.LearningConceptDetailComponent),
      },
      {
        path: 'learning/new',
        loadComponent: () =>
          import('./features/learning/learning-page.component').then((m) => m.LearningFormComponent),
      },
      {
        path: 'learning/:id/edit',
        loadComponent: () =>
          import('./features/learning/learning-page.component').then((m) => m.LearningFormComponent),
      },
      {
        path: 'career',
        loadComponent: () =>
          import('./features/career/career-page.component').then((m) => m.CareerPageComponent),
      },
      {
        path: 'finance',
        loadComponent: () =>
          import('./features/finance/finance-page.component').then((m) => m.FinancePageComponent),
      },
      {
        path: 'analytics',
        redirectTo: 'insights',
        pathMatch: 'full',
      },
      {
        path: 'analytics/dashboard',
        loadComponent: () =>
          import('./features/analytics-dashboard/analytics-dashboard-hub.component').then(
            (m) => m.AnalyticsDashboardHubComponent,
          ),
      },
      {
        path: 'insights',
        loadComponent: () =>
          import('./features/insights/insights-hub.component').then((m) => m.InsightsHubComponent),
      },
      {
        path: 'timeline',
        loadComponent: () =>
          import('./features/timeline/timeline-hub.component').then((m) => m.TimelineHubComponent),
      },
      {
        path: 'reports',
        redirectTo: 'insights?tab=reports',
        pathMatch: 'full',
      },
      {
        path: 'memory',
        loadComponent: () =>
          import('./features/memory/memory-page.component').then((m) => m.MemoryPageComponent),
      },
      {
        path: 'coaches',
        loadComponent: () =>
          import('./features/coaches/coaches-page.component').then((m) => m.CoachesPageComponent),
      },
      {
        path: 'ocr',
        redirectTo: 'documents?tab=scan',
        pathMatch: 'full',
      },
      {
        path: 'voice',
        loadComponent: () =>
          import('./features/voice/voice-page.component').then((m) => m.VoicePageComponent),
      },
      {
        path: 'integrations',
        loadComponent: () =>
          import('./features/integrations/integrations-page.component').then((m) => m.IntegrationsPageComponent),
      },
      {
        path: 'automations',
        loadComponent: () =>
          import('./features/automations/automations-page.component').then((m) => m.AutomationsPageComponent),
      },
      {
        path: 'predictions',
        redirectTo: 'insights?tab=predictions',
        pathMatch: 'full',
      },
      {
        path: 'life-timeline',
        redirectTo: 'timeline?tab=milestones',
        pathMatch: 'full',
      },
    ],
  },
  { path: '**', redirectTo: 'analytics/dashboard' },
];
