import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { CommunicationHubComponent } from './communication-hub.component';
import { CommunicationService } from './services/communication.service';
import { WritingPractice } from './models/communication.models';

const now = new Date().toISOString();
const writing: WritingPractice = {
  id: 'w1',
  title: 'Essay',
  content: 'body',
  category: 'essay',
  created_at: now,
  updated_at: now,
};

describe('CommunicationHubComponent', () => {
  let fixture: ComponentFixture<CommunicationHubComponent>;
  let component: CommunicationHubComponent;
  let communication: {
    listVocabulary: jasmine.Spy;
    listWriting: jasmine.Spy;
    listSpeaking: jasmine.Spy;
    deleteWriting: jasmine.Spy;
  };

  beforeEach(async () => {
    communication = {
      listVocabulary: jasmine.createSpy('listVocabulary').and.returnValue(of([])),
      listWriting: jasmine.createSpy('listWriting').and.returnValue(of([writing])),
      listSpeaking: jasmine.createSpy('listSpeaking').and.returnValue(of([])),
      deleteWriting: jasmine.createSpy('deleteWriting').and.returnValue(of(void 0)),
    };

    await TestBed.configureTestingModule({
      imports: [CommunicationHubComponent],
      providers: [
        provideRouter([]),
        { provide: CommunicationService, useValue: communication },
        { provide: ConfirmService, useValue: { confirm: () => Promise.resolve(true) } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CommunicationHubComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  });

  it('deletes writing from the list after confirm', async () => {
    component.setTab('writing');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Essay');
    const deleteBtn = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>
    ).find((el) => el.textContent?.includes('Delete'));
    expect(deleteBtn).toBeTruthy();
    deleteBtn!.click();
    await fixture.whenStable();
    expect(communication.deleteWriting).toHaveBeenCalledWith('w1');
  });
});
