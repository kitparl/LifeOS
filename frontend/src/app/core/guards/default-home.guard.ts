import { inject } from '@angular/core';
import { RedirectFunction } from '@angular/router';
import { HomePreferencesService } from '../services/home-preferences.service';

/** Sends `/` (and other default-home redirects) to the user's chosen module. */
export const defaultHomeRedirect: RedirectFunction = () => {
  return inject(HomePreferencesService).homeRoute();
};
