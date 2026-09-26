import { NewsLayout } from '../../../core/services/news-preferences.service';

/** Container classes per layout, shared by the feed and its loading skeleton so they line up. */
export function newsLayoutClass(layout: NewsLayout): string {
  switch (layout) {
    case 'list':
      return 'space-y-2';
    case 'grid':
      return 'grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4';
    case 'cards':
      return 'grid gap-3 sm:grid-cols-2 xl:grid-cols-3';
  }
}
