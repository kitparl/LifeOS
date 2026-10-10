import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-qa-reference-links',
  standalone: true,
  template: `
    @if (links.length) {
      <div class="mt-2 text-xs">
        <p class="mb-1" style="color: var(--text-muted)">References</p>
        <ul class="space-y-0.5">
          @for (link of links; track link) {
            <li class="break-all">
              <a [href]="link" target="_blank" rel="noopener noreferrer" class="link" (click)="$event.stopPropagation()">{{ link }}</a>
            </li>
          }
        </ul>
      </div>
    }
  `,
})
export class QAReferenceLinksComponent {
  @Input() links: string[] = [];
}
