/**
 * Every word a friend sees in the trip planner, in one place so it can be translated later
 * (requirements D-07). Plain language only: never "version", "revision", "draft" or
 * "itinerary item" (a spec checks this).
 */

import { StopKind } from '../models/share.models';

export interface QuickChip {
  kind: StopKind;
  label: string;
  icon: string;
  /** Suggested "what" when the field is still empty. */
  title: string;
}

export const QUICK_CHIPS: readonly QuickChip[] = [
  { kind: 'stay', label: 'Stay', icon: '🛏️', title: 'Stay the night' },
  { kind: 'food', label: 'Food', icon: '🍽️', title: 'Eat' },
  { kind: 'travel', label: 'Travel', icon: '🚗', title: 'Travel' },
  { kind: 'sightseeing', label: 'Sightseeing', icon: '📸', title: 'See' },
  { kind: 'rest', label: 'Rest', icon: '☕', title: 'Take a break' },
];

export const KIND_ICONS: Record<StopKind, string> = {
  stay: '🛏️',
  food: '🍽️',
  travel: '🚗',
  sightseeing: '📸',
  rest: '☕',
  other: '📍',
};

export const COPY = {
  loading: 'Opening the plan…',
  notFound: "This link doesn't work. Check you have the whole link, or ask for it again.",
  gone: 'The trip owner has turned this link off.',
  loadFailed: "We couldn't open the plan. Check your internet and try again.",
  tryAgain: 'Try again',

  tabs: { plan: 'Plan', map: 'Map', me: 'Me' },
  day: (n: number) => `Day ${n}`,
  addPlace: 'Add a place',
  addDay: 'Add a day',
  emptyDay: 'Nothing planned yet. Add a place to start.',
  emptyPlan: 'No days yet. Add a day to start planning.',
  openInMaps: 'Open in Google Maps',
  openDayInMaps: 'Day route in Google Maps',
  more: 'More',
  moveUp: (title: string) => `Move ${title} up`,
  moveDown: (title: string) => `Move ${title} down`,
  dragHandle: (title: string) => `Drag to move ${title}. Or use the arrow keys.`,
  remove: 'Remove',
  removeDay: (n: number) => `Remove day ${n}`,
  removed: (title: string) => `Removed ${title}`,
  undo: 'Undo',

  sheet: {
    addTitle: 'Add a place',
    editTitle: 'Change this stop',
    what: 'What',
    whatHint: 'For example: Lunch at the lake',
    where: 'Where',
    whereHint: 'Search a place, or paste a Google Maps link',
    time: 'Time',
    moreDetails: 'More details',
    notes: 'Notes',
    links: 'Links (one per line)',
    transport: 'How you get there',
    stay: 'Where you sleep',
    save: 'Done',
    cancel: 'Cancel',
    clearPlace: 'Remove place',
    searching: 'Searching…',
    readingLink: 'Reading the link…',
    linkNotRead: "We couldn't read that link, so we kept it. Type a name in What.",
    searchResting: 'Search is resting for now. Type the place name, or paste a Google Maps link.',
    searchOff: 'Type the place name, or paste a Google Maps link.',
    needWhat: 'Write what this stop is.',
  },

  whoTitle: 'Who are you?',
  whoIntro: (owner: string) => `So ${owner} knows whose plan this is.`,
  google: 'Continue with Google',
  privacy: (owner: string) => `${owner} will see your name and Gmail.`,
  justName: 'Just use my name',
  yourName: 'Your name',
  continueName: 'Continue',
  googleNeeded: (owner: string) => `${owner} asked everyone to continue with Google.`,
  inAppBrowser:
    "Google sign-in doesn't work inside this app. Open the link in Chrome or Safari, or just use your name.",
  copyLink: 'Copy link',
  linkCopied: 'Link copied',
  googleFailed: "Google sign-in didn't work here. You can just use your name instead.",
  nameOnlyNote:
    'Your plan is saved on this phone or computer only. Clearing the browser or switching phone loses it.',
  keepSafe: 'Sign in with Google to keep this safe',

  saved: 'Saved',
  saving: 'Saving…',
  offline: 'Offline, will retry',
  saveError: "Couldn't save. We'll keep trying.",
  conflict: 'This plan was updated on another device.',
  reload: 'Load the newer plan',
  keepMine: 'Keep mine',
  restoreTitle: 'You have changes that were not saved.',
  restore: 'Bring them back',
  discard: 'Discard',
  leaveWarning: 'Your last changes are still saving. Leave anyway?',

  sendTo: (owner: string) => `Send to ${owner}`,
  sendAgain: (owner: string) => `Send again to ${owner}`,
  sendTitle: (owner: string) => `Send your plan to ${owner}`,
  messageLabel: (owner: string) => `A note for ${owner} (optional)`,
  send: 'Send',
  sent: (owner: string) => `Sent to ${owner}. You can keep changing it and send again.`,
  sentBadge: 'Sent',
  changedSinceSent: 'Changed since you sent it',

  finalBadge: 'Final plan',
  finalNote: (owner: string) => `${owner} has chosen the final plan, so it can't be changed now. Your own plan is kept.`,
  viewingNote: (owner: string) => `This is ${owner}'s plan. Change anything to start your own.`,
  yourPlan: 'Your plan',
  ownerShortcut: 'You own this plan.',
  manage: 'Manage it',

  me: {
    title: 'You',
    signedInGoogle: (name: string) => `${name} (Google)`,
    signedInName: (name: string) => name,
    notJoined: 'You have not started a plan yet. Change anything in the plan to start yours.',
    startOver: 'Start over from the trip plan',
    startOverConfirm: 'Start over? Your changes are replaced by the trip plan. You can undo this.',
    forget: 'Forget me on this device',
    forgetConfirm: 'Forget you on this device? You will need to continue again to change your plan.',
  },
  removedNote: 'The trip owner has removed you from this plan.',
  lostAccess: 'This device no longer has access to your plan. Continue again to keep planning.',

  firstRun: [
    { title: 'This is the trip plan', body: 'Look through the days and stops. Tap Map to see where everything is.' },
    { title: 'Make it yours', body: 'Add a place, move stops up or down, or remove them. Everything saves by itself.' },
    { title: 'Send it back', body: 'When you are happy, tap Send. You can still change it after.' },
  ],
  next: 'Next',
  skip: 'Skip',
  gotIt: 'Got it',
} as const;

/** Words that must never appear in the friend UI (checked by a spec). */
export const FORBIDDEN_WORDS = ['version', 'revision', 'draft', 'itinerary item'];
