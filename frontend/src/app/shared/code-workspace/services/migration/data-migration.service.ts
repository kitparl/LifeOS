import { Injectable } from '@angular/core';
import Dexie, { Table } from 'dexie';
import { BehaviorSubject, Observable } from 'rxjs';
import {
  BackupRecord,
  MigrationProgress,
  MigrationRecord,
  ValidationResult,
} from '../../models/migration.model';
import { BackupError } from './migration.errors';
import { ContentConverterService } from './content-converter.service';

const BACKUP_TTL_DAYS = 30;
const LOCAL_STORAGE_PREFIX = 'backup:';
const LOCAL_STORAGE_ID_PREFIX = 'localStorage:';

class MigrationDB extends Dexie {
  backups!: Table<BackupRecord, string>;
  migrations!: Table<MigrationRecord, string>;

  constructor() {
    super('MigrationDB');
    this.version(1).stores({
      backups: 'id, timestamp, componentName, expiresAt',
      migrations: 'id, componentName, status, timestamp',
    });
    this.version(2).stores({
      backups: 'id, timestamp, componentName, expiresAt',
      migrations: 'id, componentName, status, timestamp, backupId',
    });
  }
}

type RestoreHandler = (content: string) => void | Promise<void>;

/**
 * Orchestrates HTML → Markdown migration with IndexedDB backups.
 */
@Injectable({ providedIn: 'root' })
export class DataMigrationService {
  private db = new MigrationDB();
  private pendingContent = new Map<string, string>();
  private restoredContent = new Map<string, string>();
  private restoreHandlers = new Map<string, RestoreHandler>();
  private progress$ = new BehaviorSubject<MigrationProgress>(this.emptyProgress());

  constructor(private converter: ContentConverterService) {
    void this.refreshProgress();
  }

  registerComponentContent(componentName: string, content: string): void {
    this.pendingContent.set(componentName, content);
  }

  registerRestoreHandler(componentName: string, handler: RestoreHandler): void {
    this.restoreHandlers.set(componentName, handler);
  }

  getRestoredContent(componentName: string): string | null {
    return this.restoredContent.get(componentName) ?? null;
  }

  /**
   * Migrates one component: backup → convert → validate → record.
   */
  async migrateComponent(
    componentName: string,
    content?: string
  ): Promise<MigrationRecord> {
    const originalContent = content ?? this.pendingContent.get(componentName);
    if (originalContent === undefined) {
      throw new Error(
        `No content registered for component "${componentName}". ` +
          'Pass HTML content or call registerComponentContent() first.'
      );
    }

    const record: MigrationRecord = {
      id: this.generateId(),
      componentName,
      originalContent,
      convertedContent: '',
      timestamp: new Date(),
      status: 'pending',
      backupId: '',
    };

    try {
      record.status = 'in-progress';
      record.backupId = await this.createBackup(componentName, originalContent);
      await this.db.migrations.put(record);
      await this.refreshProgress();

      const conversion = await this.converter.htmlToMarkdown(originalContent);
      record.convertedContent = conversion.markdown;

      const validation = this.converter.validateConversion(
        originalContent,
        conversion.markdown
      );

      if (!conversion.success || !validation.semanticEquivalent) {
        record.status = 'failed';
      } else {
        record.status = 'completed';
        this.pendingContent.delete(componentName);
      }

      await this.db.migrations.put(record);
      await this.refreshProgress();
      return record;
    } catch (error) {
      record.status = 'failed';
      await this.db.migrations.put(record).catch((storeError) => {
        console.error('Failed to persist migration record:', storeError);
      });
      await this.refreshProgress();
      throw error;
    }
  }

  async createBackup(componentName: string, content: string): Promise<string> {
    const backup: BackupRecord = {
      id: this.generateId(),
      componentName,
      content,
      timestamp: new Date(),
      expiresAt: this.addDays(new Date(), BACKUP_TTL_DAYS),
      metadata: {
        size: content.length,
        format: 'html',
      },
    };

    try {
      await this.db.backups.add(backup);
      return backup.id;
    } catch (error) {
      console.error('IndexedDB backup failed:', error);
      try {
        localStorage.setItem(
          `${LOCAL_STORAGE_PREFIX}${backup.id}`,
          JSON.stringify({
            ...backup,
            timestamp: backup.timestamp.toISOString(),
            expiresAt: backup.expiresAt.toISOString(),
          })
        );
        console.warn('Backup stored in localStorage fallback');
        return `${LOCAL_STORAGE_ID_PREFIX}${backup.id}`;
      } catch {
        throw new BackupError(
          'Failed to create backup: migration aborted',
          componentName,
          'create'
        );
      }
    }
  }

  /**
   * Restores original content from a backup and marks the migration rolled-back.
   */
  async rollback(backupId: string): Promise<boolean> {
    try {
      const backup = await this.loadBackup(backupId);
      if (!backup) {
        throw new BackupError('Backup not found', '', 'load');
      }

      await this.restoreContent(backup.componentName, backup.content);

      const backupIds = new Set([backupId, backup.id, `${LOCAL_STORAGE_ID_PREFIX}${backup.id}`]);
      await this.db.migrations
        .filter((record) => backupIds.has(record.backupId))
        .modify({ status: 'rolled-back' });

      await this.refreshProgress();
      return true;
    } catch (error) {
      console.error('Rollback failed:', error);
      return false;
    }
  }

  getProgress(): Observable<MigrationProgress> {
    void this.refreshProgress();
    return this.progress$.asObservable();
  }

  async validateMigration(record: MigrationRecord): Promise<ValidationResult> {
    return this.converter.validateConversion(
      record.originalContent,
      record.convertedContent
    );
  }

  private async refreshProgress(): Promise<void> {
    try {
      const records = await this.db.migrations.toArray();
      this.progress$.next(this.summarizeProgress(records));
    } catch (error) {
      console.error('Failed to refresh migration progress:', error);
    }
  }

  private summarizeProgress(records: MigrationRecord[]): MigrationProgress {
    const total = records.length;
    const completed = records.filter((record) => record.status === 'completed').length;
    const failed = records.filter((record) => record.status === 'failed').length;
    const inProgress = records.filter((record) => record.status === 'in-progress').length;
    return {
      total,
      completed,
      failed,
      inProgress,
      percentage: total === 0 ? 0 : Math.round((completed / total) * 1000) / 10,
    };
  }

  private emptyProgress(): MigrationProgress {
    return {
      total: 0,
      completed: 0,
      failed: 0,
      inProgress: 0,
      percentage: 0,
    };
  }

  private async restoreContent(componentName: string, content: string): Promise<void> {
    this.restoredContent.set(componentName, content);
    this.pendingContent.set(componentName, content);
    const handler = this.restoreHandlers.get(componentName);
    if (handler) {
      await handler(content);
    }
  }

  private async loadBackup(backupId: string): Promise<BackupRecord | undefined> {
    const id = backupId.startsWith(LOCAL_STORAGE_ID_PREFIX)
      ? backupId.slice(LOCAL_STORAGE_ID_PREFIX.length)
      : backupId;

    const fromDb = await this.db.backups.get(id);
    if (fromDb) {
      return this.reviveBackup(fromDb);
    }

    const raw = localStorage.getItem(`${LOCAL_STORAGE_PREFIX}${id}`);
    if (!raw) {
      return undefined;
    }

    try {
      return this.reviveBackup(JSON.parse(raw) as BackupRecord);
    } catch (error) {
      console.error('Failed to parse localStorage backup:', error);
      return undefined;
    }
  }

  private reviveBackup(backup: BackupRecord): BackupRecord {
    return {
      ...backup,
      timestamp: backup.timestamp instanceof Date ? backup.timestamp : new Date(backup.timestamp),
      expiresAt: backup.expiresAt instanceof Date ? backup.expiresAt : new Date(backup.expiresAt),
    };
  }

  private generateId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return `mig-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  }

  private addDays(date: Date, days: number): Date {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
  }
}
