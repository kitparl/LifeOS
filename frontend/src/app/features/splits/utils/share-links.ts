/**
 * Share links are built in the browser and open the person's own apps; LifeOS never
 * sends a message or picks a recipient.
 */

export function absoluteShareUrl(urlPath: string, origin: string = location.origin): string {
  return `${origin}${urlPath}`;
}

export function shareMessage(groupName: string, url: string): string {
  return `Let's split the bills for "${groupName}" on LifeOS. Add what you paid and see who owes whom: ${url}`;
}

export function shareSubject(groupName: string): string {
  return `Split the bills for ${groupName}`;
}

export function whatsappHref(message: string): string {
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}

export function mailtoHref(groupName: string, message: string): string {
  return `mailto:?subject=${encodeURIComponent(shareSubject(groupName))}&body=${encodeURIComponent(message)}`;
}
