export interface PasswordStrengthResult {
  score: 0 | 1 | 2 | 3 | 4;
  label: string;
  feedback: string[];
  entropyBits: number;
}

const COMMON_PASSWORDS = ['password', '123456', '12345678', 'qwerty', 'abc123', 'password1', '111111', 'letmein', 'admin', 'welcome', 'iloveyou'];
const LABELS = ['Very weak', 'Weak', 'Fair', 'Strong', 'Very strong'];

/** Purely local heuristic — never sent, logged, or persisted anywhere. */
export function checkPasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return { score: 0, label: 'Empty', feedback: ['Enter a password.'], entropyBits: 0 };
  }

  let charsetSize = 0;
  if (/[a-z]/.test(password)) charsetSize += 26;
  if (/[A-Z]/.test(password)) charsetSize += 26;
  if (/[0-9]/.test(password)) charsetSize += 10;
  if (/[^a-zA-Z0-9]/.test(password)) charsetSize += 32;
  const entropyBits = Math.round(password.length * Math.log2(Math.max(charsetSize, 1)));

  if (COMMON_PASSWORDS.includes(password.toLowerCase())) {
    return { score: 0, label: LABELS[0], feedback: ['This is one of the most common passwords — trivially guessed.'], entropyBits };
  }

  const feedback: string[] = [];
  if (password.length < 8) feedback.push('Use at least 8 characters.');
  if (!/[a-z]/.test(password) || !/[A-Z]/.test(password)) feedback.push('Mix uppercase and lowercase letters.');
  if (!/[0-9]/.test(password)) feedback.push('Add numbers.');
  if (!/[^a-zA-Z0-9]/.test(password)) feedback.push('Add symbols.');
  if (/(.)\1{2,}/.test(password)) feedback.push('Avoid repeating the same character.');

  let score: 0 | 1 | 2 | 3 | 4;
  if (entropyBits < 28) score = 0;
  else if (entropyBits < 36) score = 1;
  else if (entropyBits < 60) score = 2;
  else if (entropyBits < 80) score = 3;
  else score = 4;

  return { score, label: LABELS[score], feedback, entropyBits };
}
