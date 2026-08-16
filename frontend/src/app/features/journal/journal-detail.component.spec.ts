import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { JournalDetailComponent } from './journal-detail.component';
import { JournalService } from './services/journal.service';
import { JournalEntry } from './models/journal.models';

const entry = (content: string): JournalEntry => ({
  id: 'j1',
  entry_date: '2026-08-16',
  entry_type: 'morning',
  title: 'Hello',
  content,
  gratitude: '- thanks',
  wins: null,
  lessons: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
});

describe('JournalDetailComponent', () => {
  async function setup(content: string): Promise<ComponentFixture<JournalDetailComponent>> {
    await TestBed.configureTestingModule({
      imports: [JournalDetailComponent],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => 'j1' } } },
        },
        { provide: JournalService, useValue: { get: () => of(entry(content)), delete: () => of(void 0) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(JournalDetailComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture;
  }

  it('renders markdown lists for markdown entries', async () => {
    const fixture = await setup('- one');
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).toContain('<ul');
    expect(html).toContain('<li>');
    expect(html).toContain('one');
    expect(html).toContain('thanks');
  });

  it('sanitizes legacy TipTap HTML instead of treating it as markdown', async () => {
    const fixture = await setup('<p>legacy <strong>html</strong></p>');
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).toContain('legacy');
    expect(html).toContain('<strong>html</strong>');
    expect(html).not.toContain('&lt;p&gt;');
  });
});
