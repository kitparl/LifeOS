/**
 * Mirror of the server's `equal_split` for the live preview: integer paise, and the
 * first `amount % n` members (in join order) get one extra paise.
 */
export function equalSplit(amountPaise: number, memberIds: readonly string[]): Map<string, number> {
  const shares = new Map<string, number>();
  if (!memberIds.length) return shares;
  const base = Math.floor(amountPaise / memberIds.length);
  const remainder = amountPaise % memberIds.length;
  memberIds.forEach((id, index) => shares.set(id, base + (index < remainder ? 1 : 0)));
  return shares;
}
