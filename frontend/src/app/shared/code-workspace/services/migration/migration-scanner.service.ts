import { Injectable } from '@angular/core';
import {
  MigrationPriorityItem,
  RiskAssessment,
  RiskLevel,
  ScanResult,
  TipTapUsageLocation,
} from '../../models/migration.model';
import { SourceFile, scanTipTapSource } from './tiptap-source-scanner';
import scanSnapshot from './tiptap-scan-results.json';

const EFFORT_HOURS: Record<RiskLevel, { base: number; perLocation: number }> = {
  low: { base: 2, perLocation: 0.5 },
  medium: { base: 4, perLocation: 1 },
  high: { base: 8, perLocation: 2 },
};

const CRITICAL_PATH_PATTERNS = [
  /\/shared\/rich-editor/,
  /knowledge-notes/,
  /\/journal\//,
  /\/dashboard\//,
];

const IMPORTANT_PATH_PATTERNS = [
  /\/communication\//,
  /\/tasks\//,
  /\/goals\//,
  /\/habits\//,
];

const COMPLEX_DEPENDENCIES = [
  '@angular/forms',
  'NG_VALUE_ACCESSOR',
  'ControlValueAccessor',
  'FormControl',
  'ReactiveFormsModule',
  '@tiptap/core',
  '@tiptap/starter-kit',
];

const RISK_MITIGATION: Record<RiskLevel, string[]> = {
  low: [
    'Create a backup before conversion',
    'Convert HTML to Markdown with ContentConverterService',
    'Spot-check converted Markdown',
    'Run standard unit tests for the component',
  ],
  medium: [
    'Create a backup before conversion',
    'Convert and run round-trip validation',
    'Feature-flag the replacement',
    'Add integration tests for the component',
    'Roll out to a subset of users first',
  ],
  high: [
    'Create a comprehensive backup and verify restore',
    'Run extra conversion validation and manual review',
    'Ship behind a feature flag with instant rollback',
    'Add integration and E2E coverage before release',
    'Migrate last, after low- and medium-risk replacements succeed',
    'Monitor production after release',
  ],
};

/**
 * Identifies TipTap usage and scores replacement risk.
 */
@Injectable({ providedIn: 'root' })
export class MigrationScannerService {
  /**
   * Scores replacement risk from usage frequency, dependencies, and critical path.
   */
  assessRisk(location: TipTapUsageLocation): RiskAssessment {
    const factors: string[] = [];
    let score = 0;

    score += this.scoreDependencies(location, factors);
    score += this.scoreUsageFrequency(location, factors);
    score += this.scoreCriticalPath(location, factors);
    score += this.scoreUsageContext(location, factors);
    score += this.scoreDataComplexity(location, factors);

    const level = this.levelFromScore(score);
    return {
      level,
      factors,
      mitigation: [...RISK_MITIGATION[level]],
    };
  }

  /**
   * Scans registered / last-run codebase snapshot for TipTap usage.
   * Live file parsing: scanFiles(). Refresh snapshot with `node scripts/scan-tiptap.mjs`.
   */
  async scanCodebase(): Promise<ScanResult> {
    const locations = (scanSnapshot.locations as Array<Omit<TipTapUsageLocation, 'riskLevel'>>).map(
      (location) => this.withRisk(location)
    );
    return this.toScanResult(locations);
  }

  /**
   * Parses TypeScript/HTML sources for TipTap imports, templates, and Editor construction.
   */
  scanFiles(files: SourceFile[]): ScanResult {
    const locations = files.flatMap((file) =>
      scanTipTapSource(file.filePath, file.content).map((location) => this.withRisk(location))
    );
    return this.toScanResult(locations);
  }

  private withRisk(location: Omit<TipTapUsageLocation, 'riskLevel'> | TipTapUsageLocation): TipTapUsageLocation {
    const assessed: TipTapUsageLocation = {
      ...location,
      riskLevel: 'low',
    };
    assessed.riskLevel = this.assessRisk(assessed).level;
    return assessed;
  }

  private toScanResult(locations: TipTapUsageLocation[]): ScanResult {
    return {
      totalLocations: locations.length,
      locations,
      estimatedEffort: this.totalEstimatedEffort(locations),
      migrationOrder: this.generateMigrationOrder(locations),
    };
  }

  /**
   * Returns component names in migration order: low risk first, then medium, then high.
   * Within the same risk level, cheaper estimates come first.
   */
  generateMigrationOrder(locations: TipTapUsageLocation[]): string[] {
    return this.buildMigrationPlan(locations).map((item) => item.componentName);
  }

  /**
   * Ordered migration plan with estimated effort in hours per component.
   */
  buildMigrationPlan(locations: TipTapUsageLocation[]): MigrationPriorityItem[] {
    const rank: Record<RiskLevel, number> = { low: 0, medium: 1, high: 2 };
    const grouped = new Map<string, TipTapUsageLocation[]>();

    for (const location of locations) {
      const group = grouped.get(location.componentName) ?? [];
      group.push(location);
      grouped.set(location.componentName, group);
    }

    const plan: MigrationPriorityItem[] = [];

    for (const [componentName, group] of grouped) {
      const representative = group.reduce((highest, location) => {
        const next = this.assessRisk(location).level;
        const prev = this.assessRisk(highest).level;
        return rank[next] > rank[prev] ? location : highest;
      });
      const assessment = this.assessRisk(representative);

      plan.push({
        componentName,
        riskLevel: assessment.level,
        estimatedEffortHours: this.estimateEffortHours(representative, group.length),
        locationCount: group.length,
        factors: assessment.factors,
      });
    }

    return plan.sort((a, b) => {
      const riskDelta = rank[a.riskLevel] - rank[b.riskLevel];
      if (riskDelta !== 0) {
        return riskDelta;
      }
      return a.estimatedEffortHours - b.estimatedEffortHours;
    });
  }

  totalEstimatedEffort(locations: TipTapUsageLocation[]): number {
    return this.buildMigrationPlan(locations).reduce(
      (sum, item) => sum + item.estimatedEffortHours,
      0
    );
  }

  private estimateEffortHours(location: TipTapUsageLocation, locationCount: number): number {
    const assessment = this.assessRisk(location);
    const hours = EFFORT_HOURS[assessment.level];
    const extraLocations = Math.max(0, locationCount - 1) * hours.perLocation;
    const dependencyHours = Math.ceil(location.dependencies.length / 2) * 0.5;
    return Math.round((hours.base + extraLocations + dependencyHours) * 10) / 10;
  }

  private scoreDependencies(location: TipTapUsageLocation, factors: string[]): number {
    const count = location.dependencies.length;
    if (count >= 5) {
      factors.push(`High dependency count (${count})`);
      return 3;
    }
    if (count >= 2) {
      factors.push(`Moderate dependency count (${count})`);
      return 2;
    }
    factors.push(`Few dependencies (${count})`);
    return 0;
  }

  private scoreUsageFrequency(location: TipTapUsageLocation, factors: string[]): number {
    const shared = location.filePath.includes('/shared/');
    const sharedEditor = /rich-editor/i.test(location.componentName);

    if (shared || sharedEditor) {
      factors.push('High usage frequency (shared component / multiple consumers)');
      return 3;
    }

    if (location.dependencies.length >= 3) {
      factors.push('Moderate usage frequency (several collaborating dependencies)');
      return 2;
    }

    factors.push('Low usage frequency (feature-local component)');
    return 0;
  }

  private scoreCriticalPath(location: TipTapUsageLocation, factors: string[]): number {
    const haystack = `${location.filePath} ${location.componentName}`;

    if (CRITICAL_PATH_PATTERNS.some((pattern) => pattern.test(haystack))) {
      factors.push('On a critical user path (shared editor, notes, journal, or dashboard)');
      return 3;
    }

    if (IMPORTANT_PATH_PATTERNS.some((pattern) => pattern.test(haystack))) {
      factors.push('On an important feature path (communication or planning modules)');
      return 1;
    }

    factors.push('Not on a critical user path');
    return 0;
  }

  private scoreUsageContext(location: TipTapUsageLocation, factors: string[]): number {
    switch (location.usageContext) {
      case 'constructor':
      case 'method':
        factors.push(`Runtime usage context (${location.usageContext})`);
        return 2;
      case 'template':
        factors.push('Template usage context');
        return 1;
      default:
        factors.push('Import-only usage context');
        return 0;
    }
  }

  private scoreDataComplexity(location: TipTapUsageLocation, factors: string[]): number {
    const complex = location.dependencies.some((dep) =>
      COMPLEX_DEPENDENCIES.some((marker) => dep.includes(marker))
    );

    if (complex) {
      factors.push('Complex data path (forms, CVA, or TipTap HTML content)');
      return 2;
    }

    factors.push('Simple data path');
    return 0;
  }

  private levelFromScore(score: number): RiskLevel {
    if (score >= 7) {
      return 'high';
    }
    if (score >= 4) {
      return 'medium';
    }
    return 'low';
  }
}
