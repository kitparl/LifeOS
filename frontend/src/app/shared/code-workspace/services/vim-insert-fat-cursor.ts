import { Direction, EditorView, ViewPlugin, ViewUpdate } from '@codemirror/view';
import { Extension } from '@codemirror/state';
import { getCM } from '@replit/codemirror-vim';

interface CursorDrawData {
  left: number;
  top: number;
  height: number;
  lineHeight: number;
  fontFamily: string;
  fontSize: string;
  fontWeight: string;
  color: string;
  letter: string;
}

/** Draws the same salmon block cursor as Vim normal mode while in insert mode. */
export function vimInsertFatCursor(): Extension {
  return ViewPlugin.fromClass(
    class {
      private readonly layer: HTMLElement;
      private vimCleanup?: () => void;
      private insertMode = false;
      private vimHooked = false;
      private hookAttempts = 0;
      private readonly measureReq = {
        read: () => this.readCursor(),
        write: (data: CursorDrawData | null) => this.drawCursor(data),
      };

      constructor(private readonly view: EditorView) {
        this.layer = document.createElement('div');
        this.layer.className = 'cm-cursorLayer cm-vimCursorLayer cm-vimInsertCursorLayer';
        this.layer.setAttribute('aria-hidden', 'true');
        this.layer.style.animation = 'none';
        view.scrollDOM.appendChild(this.layer);
        queueMicrotask(() => this.hookVim());
      }

      private hookVim(): void {
        if (this.vimHooked) {
          return;
        }
        const cm = getCM(this.view);
        if (!cm) {
          if (this.hookAttempts++ < 100) {
            queueMicrotask(() => this.hookVim());
          }
          return;
        }

        this.vimHooked = true;
        const sync = () => {
          const vim = (cm as { state?: { vim?: { insertMode?: boolean } } }).state?.vim;
          this.setInsertMode(!!vim?.insertMode);
        };

        cm.on('vim-mode-change', sync);
        this.vimCleanup = () => cm.off('vim-mode-change', sync);
        sync();
      }

      private setInsertMode(active: boolean): void {
        this.insertMode = active;
        this.view.dom.classList.toggle('cm-vimInsertMode', active);
        if (active) {
          this.view.requestMeasure(this.measureReq);
        } else {
          this.layer.textContent = '';
        }
      }

      update(update: ViewUpdate): void {
        if (!this.vimHooked) {
          this.hookVim();
        }
        if (
          this.insertMode &&
          (update.selectionSet ||
            update.docChanged ||
            update.geometryChanged ||
            update.viewportChanged)
        ) {
          this.view.requestMeasure(this.measureReq);
        }
      }

      private readCursor(): CursorDrawData | null {
        if (!this.insertMode) {
          return null;
        }

        const head = this.view.state.selection.main.head;
        const pos = this.view.coordsAtPos(head, 1);
        if (!pos) {
          return null;
        }

        const base = this.getBase();
        const domAtPos = this.view.domAtPos(head);
        let node: Node = domAtPos?.node ?? this.view.contentDOM;

        if (node instanceof Text && domAtPos && domAtPos.offset >= node.data.length) {
          const parent = node.parentElement;
          if (parent?.nextSibling) {
            node = parent.nextSibling;
          }
        }

        let element: HTMLElement = this.view.contentDOM;
        if (node instanceof HTMLElement) {
          element = node;
        } else if (node.parentElement) {
          element = node.parentElement;
        }

        const style = getComputedStyle(element);
        let letter =
          head < this.view.state.doc.length ? this.view.state.sliceDoc(head, head + 1) : '';
        let left = pos.left;

        const coordsForChar = (
          this.view as { coordsForChar?: (position: number) => { left: number } | null }
        ).coordsForChar?.(head);
        if (coordsForChar) {
          left = coordsForChar.left;
        }

        if (!letter || letter === '\n' || letter === '\r') {
          letter = '\xa0';
        } else if (letter === '\t') {
          letter = '\xa0';
        }

        const height = pos.bottom - pos.top;
        return {
          left: (left - base.left) / this.view.scaleX,
          top: (pos.top - base.top) / this.view.scaleY,
          height,
          lineHeight: height,
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          fontWeight: style.fontWeight,
          color: style.color,
          letter,
        };
      }

      private drawCursor(data: CursorDrawData | null): void {
        if (!data || !this.insertMode) {
          this.layer.textContent = '';
          return;
        }

        let el = this.layer.querySelector('.cm-fat-cursor') as HTMLElement | null;
        if (!el) {
          el = document.createElement('div');
          el.className = 'cm-fat-cursor cm-cursor-primary';
          this.layer.appendChild(el);
        }

        el.style.left = `${data.left}px`;
        el.style.top = `${data.top}px`;
        el.style.height = `${data.height}px`;
        el.style.lineHeight = `${data.lineHeight}px`;
        el.style.fontFamily = data.fontFamily;
        el.style.fontSize = data.fontSize;
        el.style.fontWeight = data.fontWeight;
        el.style.color = data.color;
        el.style.animation = 'none';
        el.style.opacity = '1';
        el.textContent = data.letter;
      }

      private getBase(): { left: number; top: number } {
        const rect = this.view.scrollDOM.getBoundingClientRect();
        const left =
          this.view.textDirection === Direction.LTR
            ? rect.left
            : rect.right - this.view.scrollDOM.clientWidth;
        return {
          left: left - this.view.scrollDOM.scrollLeft * this.view.scaleX,
          top: rect.top - this.view.scrollDOM.scrollTop * this.view.scaleY,
        };
      }

      destroy(): void {
        this.vimCleanup?.();
        this.layer.remove();
        this.view.dom.classList.remove('cm-vimInsertMode');
      }
    },
  );
}
