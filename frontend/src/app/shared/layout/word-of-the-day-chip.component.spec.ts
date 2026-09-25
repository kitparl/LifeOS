import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { VocabularyDetail } from '../../features/communication/vocabulary/models/vocabulary.models';
import { WordOfTheDayService } from '../../features/communication/vocabulary/services/word-of-the-day.service';
import { WordOfTheDayChipComponent } from './word-of-the-day-chip.component';

const WORD = {
  id: 'w20260925',
  term: 'herald',
  part_of_speech: 'noun',
  simple_meaning: 'A messenger bearing news.',
  example: 'The herald announced the king.',
  synonyms: ['envoy'],
} as VocabularyDetail;

describe('WordOfTheDayChipComponent', () => {
  let fixture: ComponentFixture<WordOfTheDayChipComponent>;
  const word = signal<VocabularyDetail | null>(null);
  const wotd = { word, load: jasmine.createSpy('load') };
  const router = { navigate: jasmine.createSpy('navigate') };

  beforeEach(async () => {
    word.set(null);
    wotd.load.calls.reset();
    router.navigate.calls.reset();
    await TestBed.configureTestingModule({
      imports: [WordOfTheDayChipComponent],
      providers: [
        { provide: WordOfTheDayService, useValue: wotd },
        { provide: AuthService, useValue: { user: signal({ id: 'user-1' }) } },
        { provide: Router, useValue: router },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(WordOfTheDayChipComponent);
    fixture.detectChanges();
  });

  function chip(): HTMLButtonElement | null {
    return fixture.nativeElement.querySelector('button.chip');
  }

  it('loads for the signed-in user and stays hidden without a word', () => {
    expect(wotd.load).toHaveBeenCalledWith('user-1');
    expect(chip()).toBeNull();
  });

  it('opens the popover on hover and closes it with Escape', () => {
    word.set(WORD);
    fixture.detectChanges();
    fixture.nativeElement.dispatchEvent(new MouseEvent('mouseenter'));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('A messenger bearing news.');
    expect(chip()!.getAttribute('aria-expanded')).toBe('true');

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('#wotd-popover')).toBeNull();
  });

  it('navigates to the vocabulary detail page on click', () => {
    word.set(WORD);
    fixture.detectChanges();
    chip()!.click();
    expect(router.navigate).toHaveBeenCalledWith(['/communication/vocabulary', 'w20260925']);
  });

  it('first tap opens the popover, second tap navigates (touch)', () => {
    word.set(WORD);
    fixture.detectChanges();
    fixture.componentInstance.lastPointer = 'touch';
    chip()!.click();
    fixture.detectChanges();
    expect(router.navigate).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('#wotd-popover')).not.toBeNull();
    chip()!.click();
    expect(router.navigate).toHaveBeenCalled();
  });

  it('shows only the term in the header', () => {
    word.set(WORD);
    fixture.detectChanges();
    expect(chip()!.textContent!.trim()).toBe('herald');
    expect(chip()!.getAttribute('aria-label')).toBe('Word of the Day: herald');
  });

  it('keeps the popover open through a brief pointer slip and closes after the delay', fakeAsync(() => {
    word.set(WORD);
    fixture.detectChanges();
    const host: HTMLElement = fixture.nativeElement;
    host.dispatchEvent(new MouseEvent('mouseenter'));
    host.dispatchEvent(new MouseEvent('mouseleave'));
    tick(150);
    host.dispatchEvent(new MouseEvent('mouseenter'));
    tick(500);
    fixture.detectChanges();
    expect(host.querySelector('#wotd-popover')).not.toBeNull();

    host.dispatchEvent(new MouseEvent('mouseleave'));
    tick(299);
    fixture.detectChanges();
    expect(host.querySelector('#wotd-popover')).not.toBeNull();
    tick(1);
    fixture.detectChanges();
    expect(host.querySelector('#wotd-popover')).toBeNull();
  }));
});
