import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { HashAlgo, OUTDATED_HASH_ALGOS, computeHash } from './hash.util';

const ALGOS: HashAlgo[] = ['MD5', 'SHA-1', 'SHA-256', 'SHA-512'];

@Component({
  selector: 'app-hash-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="hash-generator"
      title="Hash Generator"
      description="Generate MD5, SHA-1, SHA-256, or SHA-512 hashes locally using the Web Crypto API. Nothing is sent to a server."
      icon="hash"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="flex items-center gap-2">
          <label class="form-label !mb-0">Algorithm</label>
          <select class="input-field w-auto" [ngModel]="algo()" (ngModelChange)="setAlgo($event)">
            @for (a of algos; track a) {
              <option [ngValue]="a">{{ a }}</option>
            }
          </select>
          @if (isOutdated()) {
            <span class="badge" style="background: var(--warning-soft); color: var(--warning);">Not recommended for security use</span>
          }
        </div>
        <app-copy-button [text]="output()" />
      </div>

      <div class="space-y-1">
        <label class="form-label">Input text</label>
        <textarea
          class="input-field h-40 resize-y font-mono text-sm"
          placeholder="Type or paste text to hash…"
          [ngModel]="input()"
          (ngModelChange)="onInputChange($event)"
        ></textarea>
      </div>
      <div class="mt-3 space-y-1">
        <label class="form-label">{{ algo() }} hash</label>
        <input class="input-field font-mono text-sm" readonly [ngModel]="output()" />
      </div>
    </app-dev-tool-shell>
  `,
})
export class HashGeneratorToolComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);

  readonly algos = ALGOS;
  readonly algo = signal<HashAlgo>('SHA-256');
  readonly input = signal('');
  readonly output = signal('');

  readonly isOutdated = () => OUTDATED_HASH_ALGOS.includes(this.algo());

  ngOnInit(): void {
    const requested = (this.route.snapshot.queryParamMap.get('algo') ?? '').toUpperCase();
    const match = ALGOS.find((a) => a.toUpperCase() === requested || a.replace('-', '').toUpperCase() === requested);
    if (match) this.algo.set(match);
    this.run();
  }

  setAlgo(value: HashAlgo): void {
    this.algo.set(value);
    this.run();
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.run();
  }

  private run(): void {
    if (!this.input()) {
      this.output.set('');
      return;
    }
    computeHash(this.algo(), this.input()).then((hash) => this.output.set(hash));
  }
}
