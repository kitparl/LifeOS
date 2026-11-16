import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { TypeSelectComponent } from './type-select.component';

@Component({
  standalone: true,
  imports: [ReactiveFormsModule, TypeSelectComponent],
  template: `<app-type-select [formControl]="control" [multiple]="true" [options]="options" />`,
})
class MultiHostComponent {
  control = new FormControl<string[]>(['AIMS Certified'], { nonNullable: true });
  options = ['AIMS Certified', 'AbbottWMM', 'SheRACES'];
}

describe('TypeSelectComponent (multiple)', () => {
  let fixture: ComponentFixture<MultiHostComponent>;
  let host: MultiHostComponent;
  let select: TypeSelectComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [MultiHostComponent] }).compileComponents();
    fixture = TestBed.createComponent(MultiHostComponent);
    host = fixture.componentInstance;
    fixture.detectChanges();
    select = fixture.debugElement.children[0].componentInstance as TypeSelectComponent;
  });

  it('renders the initial values as tags', () => {
    const tags = fixture.nativeElement.querySelectorAll('.type-select__tag');
    expect(tags.length).toBe(1);
    expect(tags[0].textContent).toContain('AIMS Certified');
  });

  it('toggles options in and out of the selection', () => {
    select.select('SheRACES');
    expect(host.control.value).toEqual(['AIMS Certified', 'SheRACES']);

    select.select('AIMS Certified');
    expect(host.control.value).toEqual(['SheRACES']);
  });

  it('adds a created value to the selection', () => {
    select.query.set('Gold Label');
    select.createNew();
    expect(host.control.value).toEqual(['AIMS Certified', 'Gold Label']);
  });

  it('clears to an empty array', () => {
    select.clear();
    expect(host.control.value).toEqual([]);
  });
});
