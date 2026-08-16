import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { FilesService } from '../../features/files/services/files.service';
import { FileImageSrcDirective } from './file-image-src.directive';

@Component({
  standalone: true,
  imports: [FileImageSrcDirective],
  template: `<div appFileImageSrc [innerHTML]="html"></div>`,
})
class HostComponent {
  html = '';
}

describe('FileImageSrcDirective', () => {
  let fixture: ComponentFixture<HostComponent>;
  let files: { tokenUrl: jasmine.Spy };

  beforeEach(async () => {
    files = {
      tokenUrl: jasmine.createSpy('tokenUrl').and.callFake((id: string) => of(`https://files.test/${id}?token=abc`)),
    };
    await TestBed.configureTestingModule({
      imports: [HostComponent],
      providers: [{ provide: FilesService, useValue: files }],
    }).compileComponents();
    fixture = TestBed.createComponent(HostComponent);
  });

  it('rewrites private file img src to a token URL', async () => {
    fixture.componentInstance.html =
      '<img src="/api/v1/files/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/content" alt="shot">';
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const img = fixture.nativeElement.querySelector('img') as HTMLImageElement;
    expect(files.tokenUrl).toHaveBeenCalledWith('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee');
    expect(img.getAttribute('src')).toContain('token=abc');
  });
});
