import { GameVocabularyItem } from '../models/vocabulary.models';

export interface McQuestion {
  vocabularyId: string;
  term: string;
  prompt: string;
  options: string[];
  correctIndex: number;
}

export interface MatchPair {
  vocabularyId: string;
  left: string;
  right: string;
}

function shuffled<T>(arr: T[]): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function pickDistractors(pool: string[], exclude: string, count: number): string[] {
  const candidates = shuffled(pool.filter((v) => v !== exclude));
  return candidates.slice(0, count);
}

function blankTerm(example: string, term: string): string {
  const pattern = new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
  return example.replace(pattern, '____');
}

/** Every multiple-choice-shaped game type (meaning/synonym/antonym quiz, fill-in-blank,
 * example completion) reuses this one builder with a different field/prompt mapping —
 * one engine, seven named types, per the requirements doc's design decision. */
export function buildMcQuestions(
  pool: GameVocabularyItem[],
  gameType: 'meaning_quiz' | 'synonym_quiz' | 'antonym_quiz' | 'fill_in_blank' | 'example_completion',
  count: number,
): McQuestion[] {
  let candidates: GameVocabularyItem[];
  let answerField: (item: GameVocabularyItem) => string | null;
  let promptFor: (item: GameVocabularyItem) => string;

  switch (gameType) {
    case 'synonym_quiz':
      candidates = pool.filter((i) => i.synonyms.length > 0);
      answerField = (i) => i.synonyms[0] ?? null;
      promptFor = (i) => `Which word is a synonym of "${i.term}"?`;
      break;
    case 'antonym_quiz':
      candidates = pool.filter((i) => i.antonyms.length > 0);
      answerField = (i) => i.antonyms[0] ?? null;
      promptFor = (i) => `Which word is an antonym of "${i.term}"?`;
      break;
    case 'fill_in_blank':
      candidates = pool;
      answerField = (i) => i.term;
      promptFor = (i) => blankTerm(i.example, i.term);
      break;
    case 'example_completion':
      candidates = pool;
      answerField = (i) => i.term;
      promptFor = (i) => `"${i.simple_meaning}" — ${blankTerm(i.example, i.term)}`;
      break;
    default:
      candidates = pool;
      answerField = (i) => i.simple_meaning;
      promptFor = (i) => `What does "${i.term}" mean?`;
  }

  const answerPool = candidates.map(answerField).filter((v): v is string => !!v);
  const chosen = shuffled(candidates).slice(0, count);

  return chosen
    .map((item) => {
      const correct = answerField(item);
      if (!correct) return null;
      const distractors = pickDistractors(answerPool, correct, 3);
      const options = shuffled([correct, ...distractors]);
      return {
        vocabularyId: item.id,
        term: item.term,
        prompt: promptFor(item),
        options,
        correctIndex: options.indexOf(correct),
      };
    })
    .filter((q): q is McQuestion => q !== null);
}

/** word_matching (term <-> meaning) and meaning_matching (term <-> synonym, falling back
 * to meaning when an item has no synonym) share this one pairs builder. */
export function buildMatchPairs(
  pool: GameVocabularyItem[],
  gameType: 'word_matching' | 'meaning_matching',
  count: number,
): MatchPair[] {
  const items = shuffled(pool).slice(0, count);
  return items.map((item) => ({
    vocabularyId: item.id,
    left: item.term,
    right: gameType === 'meaning_matching' ? (item.synonyms[0] ?? item.simple_meaning) : item.simple_meaning,
  }));
}
