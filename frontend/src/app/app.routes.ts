import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

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
    path: 'register',
    loadComponent: () => import('./features/auth/register.component').then((m) => m.RegisterComponent),
    canActivate: [guestGuard],
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
        path: 'communication/vocabulary/new',
        loadComponent: () =>
          import('./features/communication/vocabulary-form.component').then((m) => m.VocabularyFormComponent),
      },
      {
        path: 'communication/vocabulary/:id/edit',
        loadComponent: () =>
          import('./features/communication/vocabulary-form.component').then((m) => m.VocabularyFormComponent),
      },
      {
        path: 'communication/vocabulary/:id',
        loadComponent: () =>
          import('./features/communication/vocabulary-detail.component').then((m) => m.VocabularyDetailComponent),
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
