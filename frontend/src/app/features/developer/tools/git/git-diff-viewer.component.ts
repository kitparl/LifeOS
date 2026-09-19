import { Component } from '@angular/core';
import { DiffToolComponent } from '../dev-utils/diff.component';

@Component({
  selector: 'app-git-diff-viewer-tool',
  standalone: true,
  imports: [DiffToolComponent],
  template: `
    <app-diff-tool
      toolId="git-diff-viewer"
      title="Git Diff Viewer"
      description="Paste two versions of a file to view a git-style diff, side-by-side or unified."
    />
  `,
})
export class GitDiffViewerToolComponent {}
