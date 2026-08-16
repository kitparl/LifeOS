import { Injectable, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';
import Dexie, { Table } from 'dexie';
import { EditorDocument } from '../models/editor-document.model';

/**
 * IndexedDB schema for editor drafts
 */
interface DraftRecord {
  id: string;
  content: string;
  updatedAt: string;
  metadata?: any;
}

/**
 * Dexie database for editor persistence
 */
class EditorDatabase extends Dexie {
  drafts!: Table<DraftRecord, string>;

  constructor() {
    super('EditorWorkspaceDB');
    
    this.version(1).stores({
      drafts: 'id, updatedAt',
    });
  }
}

/**
 * Editor persistence service with autosave and draft management.
 * 
 * Features:
 * - Debounced autosave (2-3 seconds)
 * - IndexedDB storage via Dexie (immediate)
 * - Backend sync (queued when online)
 * - Draft recovery on reload
 * - Conflict resolution for multi-device
 * 
 * Strategy:
 * - Local-first: Save to IndexedDB immediately
 * - Backend sync: Queue for backend when online
 * - Offline-capable: Works without network
 */
@Injectable({
  providedIn: 'root'
})
export class EditorPersistenceService implements OnDestroy {
  private db: EditorDatabase;
  private autosaveSubscriptions = new Map<string, Subject<void>>();
  private destroy$ = new Subject<void>();
  private readonly AUTOSAVE_DEBOUNCE_MS = 2500; // 2.5 seconds
  private readonly API_ENDPOINT = '/api/editor/documents';

  constructor(private http: HttpClient) {
    this.db = new EditorDatabase();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    
    // Clean up all autosave subscriptions
    this.autosaveSubscriptions.forEach(sub => sub.complete());
    this.autosaveSubscriptions.clear();
  }

  // ========== AUTOSAVE ==========

  /**
   * Enable autosave for a document.
   * Content changes will be debounced and saved automatically.
   */
  enableAutosave(documentId: string, content$: Observable<string>): void {
    // If already enabled, disable first
    if (this.autosaveSubscriptions.has(documentId)) {
      this.disableAutosave(documentId);
    }

    const cancel$ = new Subject<void>();
    this.autosaveSubscriptions.set(documentId, cancel$);

    content$
      .pipe(
        debounceTime(this.AUTOSAVE_DEBOUNCE_MS),
        distinctUntilChanged(),
        takeUntil(cancel$),
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: async (content) => {
          await this.saveDraft(documentId, content);
          console.log(`Autosaved draft: ${documentId}`);
        },
        error: (error) => {
          console.error('Autosave error:', error);
        }
      });
  }

  /**
   * Disable autosave for a document
   */
  disableAutosave(documentId: string): void {
    const cancel$ = this.autosaveSubscriptions.get(documentId);
    if (cancel$) {
      cancel$.next();
      cancel$.complete();
      this.autosaveSubscriptions.delete(documentId);
    }
  }

  // ========== DRAFT MANAGEMENT ==========

  /**
   * Save draft to IndexedDB
   */
  async saveDraft(documentId: string, content: string): Promise<void> {
    try {
      const draft: DraftRecord = {
        id: documentId,
        content,
        updatedAt: new Date().toISOString(),
      };

      await this.db.drafts.put(draft);
    } catch (error) {
      console.error('Failed to save draft:', error);
      throw error;
    }
  }

  /**
   * Load draft from IndexedDB
   */
  async loadDraft(documentId: string): Promise<string | null> {
    try {
      const draft = await this.db.drafts.get(documentId);
      return draft ? draft.content : null;
    } catch (error) {
      console.error('Failed to load draft:', error);
      return null;
    }
  }

  /**
   * Clear draft from IndexedDB
   */
  async clearDraft(documentId: string): Promise<void> {
    try {
      await this.db.drafts.delete(documentId);
    } catch (error) {
      console.error('Failed to clear draft:', error);
      throw error;
    }
  }

  /**
   * Get all drafts
   */
  async getAllDrafts(): Promise<DraftRecord[]> {
    try {
      return await this.db.drafts.toArray();
    } catch (error) {
      console.error('Failed to get all drafts:', error);
      return [];
    }
  }

  /**
   * Check if draft exists
   */
  async hasDraft(documentId: string): Promise<boolean> {
    try {
      const draft = await this.db.drafts.get(documentId);
      return draft !== undefined;
    } catch (error) {
      console.error('Failed to check draft:', error);
      return false;
    }
  }

  /**
   * Get draft metadata (last updated time)
   */
  async getDraftMetadata(documentId: string): Promise<{ updatedAt: string } | null> {
    try {
      const draft = await this.db.drafts.get(documentId);
      return draft ? { updatedAt: draft.updatedAt } : null;
    } catch (error) {
      console.error('Failed to get draft metadata:', error);
      return null;
    }
  }

  // ========== BACKEND SYNC ==========

  /**
   * Sync draft to backend (when online)
   */
  async syncToBackend(documentId: string, content: string): Promise<void> {
    try {
      const document: EditorDocument = {
        id: documentId,
        title: 'Untitled',
        content,
        format: 'markdown',
        updatedAt: new Date().toISOString(),
      };

      await this.http.post(`${this.API_ENDPOINT}/${documentId}`, document).toPromise();
      console.log(`Synced to backend: ${documentId}`);
    } catch (error) {
      console.error('Backend sync failed:', error);
      // Queue for retry (could implement retry logic here)
      throw error;
    }
  }

  /**
   * Load document from backend
   */
  async loadFromBackend(documentId: string): Promise<EditorDocument | null> {
    try {
      const document = await this.http.get<EditorDocument>(
        `${this.API_ENDPOINT}/${documentId}`
      ).toPromise();
      return document || null;
    } catch (error) {
      console.error('Backend load failed:', error);
      return null;
    }
  }

  /**
   * Conflict resolution: Merge local draft with backend version
   * 
   * Strategy: Last-write-wins with user confirmation
   */
  async resolveConflict(
    documentId: string,
    localContent: string,
    localUpdatedAt: string,
    backendUpdatedAt: string
  ): Promise<'local' | 'backend' | 'merge'> {
    // Simple strategy: Compare timestamps
    const localDate = new Date(localUpdatedAt).getTime();
    const backendDate = new Date(backendUpdatedAt).getTime();

    if (localDate > backendDate) {
      return 'local';
    } else if (backendDate > localDate) {
      return 'backend';
    } else {
      return 'merge';
    }
  }

  // ========== FILE IMPORT/EXPORT ==========

  /**
   * Import file content
   */
  async importFile(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      
      reader.onerror = (e) => {
        reject(new Error('Failed to read file'));
      };
      
      reader.readAsText(file);
    });
  }

  /**
   * Export content to file
   */
  async exportFile(
    content: string,
    filename: string,
    mimeType: string = 'text/plain'
  ): Promise<void> {
    try {
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  }

  /**
   * Copy content to clipboard
   */
  async copyToClipboard(content: string): Promise<void> {
    try {
      await navigator.clipboard.writeText(content);
    } catch (error) {
      // Fallback for older browsers
      this.fallbackCopyToClipboard(content);
    }
  }

  /**
   * Fallback clipboard copy for older browsers
   */
  private fallbackCopyToClipboard(content: string): void {
    const textArea = document.createElement('textarea');
    textArea.value = content;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
      document.execCommand('copy');
    } catch (error) {
      console.error('Fallback copy failed:', error);
      throw error;
    }
    
    document.body.removeChild(textArea);
  }

  // ========== CLEANUP ==========

  /**
   * Clear all drafts (use with caution)
   */
  async clearAllDrafts(): Promise<void> {
    try {
      await this.db.drafts.clear();
    } catch (error) {
      console.error('Failed to clear all drafts:', error);
      throw error;
    }
  }

  /**
   * Delete old drafts (older than specified days)
   */
  async deleteOldDrafts(daysOld: number = 30): Promise<number> {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - daysOld);
      const cutoffISO = cutoffDate.toISOString();

      const oldDrafts = await this.db.drafts
        .where('updatedAt')
        .below(cutoffISO)
        .toArray();

      await this.db.drafts
        .where('updatedAt')
        .below(cutoffISO)
        .delete();

      return oldDrafts.length;
    } catch (error) {
      console.error('Failed to delete old drafts:', error);
      return 0;
    }
  }
}
