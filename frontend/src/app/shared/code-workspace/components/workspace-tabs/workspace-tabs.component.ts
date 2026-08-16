import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

export type WorkspaceTab = 'edit' | 'preview' | 'output';

/**
 * Mobile tab navigation component for switching between editor views.
 * 
 * Features:
 * - Three tabs: Edit | Preview | Output
 * - State preservation when switching
 * - Touch-optimized targets
 * - Custom Tailwind styling
 * - Accessibility support
 * 
 * Only visible on mobile/tablet devices (controlled by parent)
 */
@Component({
  selector: 'app-workspace-tabs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './workspace-tabs.component.html',
  styleUrls: ['./workspace-tabs.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WorkspaceTabsComponent {
  /**
   * Currently active tab
   */
  @Input() activeTab: WorkspaceTab = 'edit';

  /**
   * Whether to show the preview tab
   */
  @Input() showPreview: boolean = true;

  /**
   * Whether to show the output tab
   */
  @Input() showOutput: boolean = true;

  /**
   * Emits when tab changes
   */
  @Output() tabChange = new EventEmitter<WorkspaceTab>();

  /**
   * Handle tab click
   */
  onTabClick(tab: WorkspaceTab): void {
    if (tab !== this.activeTab) {
      this.tabChange.emit(tab);
    }
  }

  /**
   * Check if tab is active
   */
  isActive(tab: WorkspaceTab): boolean {
    return this.activeTab === tab;
  }

  /**
   * Get tab label
   */
  getTabLabel(tab: WorkspaceTab): string {
    const labels: Record<WorkspaceTab, string> = {
      'edit': 'Edit',
      'preview': 'Preview',
      'output': 'Output',
    };
    return labels[tab];
  }

  /**
   * Get tab icon SVG path
   */
  getTabIcon(tab: WorkspaceTab): string {
    // Return icon identifier for template
    return tab;
  }

  /**
   * Get visible tabs
   */
  getVisibleTabs(): WorkspaceTab[] {
    const tabs: WorkspaceTab[] = ['edit'];
    
    if (this.showPreview) {
      tabs.push('preview');
    }
    
    if (this.showOutput) {
      tabs.push('output');
    }

    return tabs;
  }
}
