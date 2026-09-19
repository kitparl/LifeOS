import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-image-renderer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="image-renderer">
      <img
        [src]="src"
        [alt]="alt"
        [style.transform]="'scale(' + zoom + ') rotate(' + rotation + 'deg)'"
      />
    </div>
  `,
  styles: [
    `
      .image-renderer {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        overflow: auto;
      }
      img {
        max-width: 100%;
        max-height: 100%;
        transition: transform 0.15s ease;
      }
    `,
  ],
})
export class ImageRendererComponent {
  @Input({ required: true }) src!: string;
  @Input() alt = '';
  @Input() zoom = 1;
  @Input() rotation = 0;
}
