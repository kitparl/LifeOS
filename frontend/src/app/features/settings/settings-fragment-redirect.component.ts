import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-settings-fragment-redirect',
  standalone: true,
  template: '',
})
export class SettingsFragmentRedirectComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  ngOnInit(): void {
    const fragment = this.route.snapshot.data['fragment'] as string | undefined;
    void this.router.navigate(['/settings'], { fragment: fragment ?? undefined });
  }
}
