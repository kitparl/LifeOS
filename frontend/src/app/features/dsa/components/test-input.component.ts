import { Component, computed, input } from '@angular/core';
import { JsonValue, SignatureSpec, formatJson, inputFields, splitInput } from '../models/dsa.models';

/** A test input shown one labelled line per field (`nums = [2,7]`), or as raw JSON if it doesn't fit the signature. */
@Component({
  selector: 'app-dsa-test-input',
  standalone: true,
  template: `
    <div class="max-h-40 space-y-0.5 overflow-auto">
      @for (row of rows(); track $index) {
        <div><span style="color: var(--text-muted)">{{ row.name }} =</span> <code class="break-all">{{ row.value }}</code></div>
      }
    </div>
  `,
})
export class TestInputComponent {
  readonly signature = input<SignatureSpec | null>(null);
  readonly value = input.required<JsonValue>();

  readonly rows = computed(() => {
    const signature = this.signature();
    const values = splitInput(signature, this.value());
    if (values === null) return [{ name: 'input', value: formatJson(this.value()) }];
    const fields = inputFields(signature);
    return values.map((v, i) => ({ name: fields[i].name, value: formatJson(v) }));
  });
}
