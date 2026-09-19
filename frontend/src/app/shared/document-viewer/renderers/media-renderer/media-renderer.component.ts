import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-media-renderer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="media-renderer">
      @if (kind === 'video') {
        <video [src]="src" controls></video>
      } @else {
        <audio [src]="src" controls></audio>
      }
    </div>
  `,
  styles: [
    `
      .media-renderer {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
      }
      video {
        max-width: 100%;
        max-height: 100%;
      }
      audio {
        width: 100%;
        max-width: 480px;
      }
    `,
  ],
})
export class MediaRendererComponent {
  @Input({ required: true }) src!: string;
  @Input({ required: true }) kind!: 'video' | 'audio';
}
