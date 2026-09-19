import { Component } from '@angular/core';
import { TextTransformToolComponent } from '../../shared/text-transform-tool.component';
import { ipv4ToIpv6Mapped, ipv6MappedToIpv4 } from './ipv4-ipv6.util';

@Component({
  selector: 'app-ipv4-ipv6-converter-tool',
  standalone: true,
  imports: [TextTransformToolComponent],
  template: `
    <app-text-transform-tool
      toolId="ipv4-ipv6-converter"
      title="IPv4 ↔ IPv6 Converter"
      description="Convert an IPv4 address to its IPv4-mapped IPv6 form, and back."
      icon="network"
      forwardLabel="IPv4 → IPv6"
      backwardLabel="IPv6 → IPv4"
      [encodeFn]="toV6"
      [decodeFn]="toV4"
      placeholder="192.168.1.1"
    />
  `,
})
export class Ipv4Ipv6ConverterToolComponent {
  readonly toV6 = ipv4ToIpv6Mapped;
  readonly toV4 = ipv6MappedToIpv4;
}
