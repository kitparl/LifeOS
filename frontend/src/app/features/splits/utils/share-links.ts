import { ShareText } from '../../../shared/share/share-links';

export function shareMessage(groupName: string, url: string): string {
  return `Let's split the bills for "${groupName}" on LifeOS. Add what you paid and see who owes whom: ${url}`;
}

export function shareSubject(groupName: string): string {
  return `Split the bills for ${groupName}`;
}

export const SPLIT_SHARE_TEXT: ShareText = {
  heading: 'Invite people with this link',
  shareLabel: 'Share invite',
  qrHint: 'Friends can scan this to open the group.',
  filePrefix: 'split',
  subject: shareSubject,
  message: shareMessage,
};
