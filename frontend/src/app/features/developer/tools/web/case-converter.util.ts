function splitWords(input: string): string[] {
  return input
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-.]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.toLowerCase());
}

export interface CaseConversions {
  lowercase: string;
  uppercase: string;
  titleCase: string;
  camelCase: string;
  pascalCase: string;
  snakeCase: string;
  kebabCase: string;
  screamingSnakeCase: string;
  dotCase: string;
}

export function convertAllCases(input: string): CaseConversions {
  const words = splitWords(input);
  const capitalized = words.map((w) => w[0]?.toUpperCase() + w.slice(1));
  return {
    lowercase: input.toLowerCase(),
    uppercase: input.toUpperCase(),
    titleCase: capitalized.join(' '),
    camelCase: words.map((w, i) => (i === 0 ? w : w[0]?.toUpperCase() + w.slice(1))).join(''),
    pascalCase: capitalized.join(''),
    snakeCase: words.join('_'),
    kebabCase: words.join('-'),
    screamingSnakeCase: words.join('_').toUpperCase(),
    dotCase: words.join('.'),
  };
}
