import { AbstractControl, AsyncValidatorFn, ValidationErrors, ValidatorFn } from '@angular/forms';
import { Observable, of, timer } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { RESERVED_USERNAMES, USERNAME_FORMAT } from '../constants/reserved-usernames';
import { UsernameService } from '../services/username.service';

export function normalizeUsername(value: string): string {
  return (value || '').trim().toLowerCase();
}

export function usernameFormatValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const raw = control.value as string;
    if (raw == null || String(raw).trim() === '') {
      return { required: true };
    }
    const username = normalizeUsername(raw);
    if (username.length < 3) {
      return { usernameFormat: 'Username must be at least 3 characters' };
    }
    if (username.length > 30) {
      return { usernameFormat: 'Username must be at most 30 characters' };
    }
    if (/\s/.test(username)) {
      return { usernameFormat: 'Username cannot contain spaces' };
    }
    if (!/^[a-z]/.test(username)) {
      return { usernameFormat: 'Username must start with a letter' };
    }
    if (/[._]$/.test(username)) {
      return { usernameFormat: 'Username cannot end with a period or underscore' };
    }
    if (/[._]{2}/.test(username)) {
      return { usernameFormat: 'Username cannot contain consecutive periods or underscores' };
    }
    if (!USERNAME_FORMAT.test(username)) {
      return {
        usernameFormat: 'Username may only contain letters, numbers, periods, and underscores',
      };
    }
    if (RESERVED_USERNAMES.has(username)) {
      return { usernameReserved: 'This username is reserved' };
    }
    return null;
  };
}

export function usernameAvailableValidator(
  usernameService: UsernameService,
  options?: { currentUsername?: () => string | null | undefined },
): AsyncValidatorFn {
  return (control: AbstractControl): Observable<ValidationErrors | null> => {
    if (control.invalid && (control.errors?.['required'] || control.errors?.['usernameFormat'] || control.errors?.['usernameReserved'])) {
      return of(null);
    }
    const username = normalizeUsername(String(control.value ?? ''));
    const current = options?.currentUsername?.()?.toLowerCase();
    if (current && username === current) {
      return of(null);
    }
    return timer(400).pipe(
      switchMap(() => usernameService.checkAvailability(username)),
      map((res) => (res.available ? null : { usernameTaken: res.reason || 'Username already taken' })),
      catchError(() => of({ usernameTaken: 'Could not check username availability' })),
    );
  };
}

export function usernameErrorMessage(control: AbstractControl | null): string | null {
  if (!control || !control.errors) {
    return null;
  }
  const e = control.errors;
  if (e['required']) return 'Username is required';
  if (e['usernameFormat']) return String(e['usernameFormat']);
  if (e['usernameReserved']) return String(e['usernameReserved']);
  if (e['usernameTaken']) return String(e['usernameTaken']);
  return null;
}
