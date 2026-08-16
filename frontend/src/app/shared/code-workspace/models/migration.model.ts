export type RiskLevel = 'low' | 'medium' | 'high';

export type UsageContext = 'import' | 'template' | 'constructor' | 'method';

export interface TipTapUsageLocation {
  componentName: string;
  filePath: string;
  lineNumber: number;
  usageContext: UsageContext;
  riskLevel: RiskLevel;
  dependencies: string[];
}

export interface ScanResult {
  totalLocations: number;
  locations: TipTapUsageLocation[];
  estimatedEffort: number;
  migrationOrder: string[];
}

export interface RiskAssessment {
  level: RiskLevel;
  factors: string[];
  mitigation: string[];
}

export interface MigrationPriorityItem {
  componentName: string;
  riskLevel: RiskLevel;
  estimatedEffortHours: number;
  locationCount: number;
  factors: string[];
}

export interface ConversionOptions {
  preserveWhitespace: boolean;
  codeBlockLanguage: string | null;
  linkStyle: 'inline' | 'reference';
  bulletMarker: '*' | '-' | '+';
  headingStyle: 'atx' | 'setext';
}

export interface ConversionResult {
  markdown: string;
  success: boolean;
  warnings: string[];
  metadata: {
    originalLength: number;
    markdownLength: number;
    elementsConverted: number;
  };
}

export interface ValidationResult {
  valid: boolean;
  differences: string[];
  semanticEquivalent: boolean;
}

export type MigrationStatus =
  | 'pending'
  | 'in-progress'
  | 'completed'
  | 'failed'
  | 'rolled-back';

export interface MigrationRecord {
  id: string;
  componentName: string;
  originalContent: string;
  convertedContent: string;
  timestamp: Date;
  status: MigrationStatus;
  backupId: string;
}

export interface BackupRecord {
  id: string;
  componentName: string;
  content: string;
  timestamp: Date;
  expiresAt: Date;
  metadata: {
    size: number;
    format: 'html' | 'markdown';
  };
}

export interface MigrationProgress {
  total: number;
  completed: number;
  failed: number;
  inProgress: number;
  percentage: number;
}
