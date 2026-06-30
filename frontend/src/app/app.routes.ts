import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
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
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./features/profile/profile.component').then((m) => m.ProfileComponent),
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
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
