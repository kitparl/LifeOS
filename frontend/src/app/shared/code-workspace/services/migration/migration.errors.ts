export class ContentConversionError extends Error {
  constructor(
    message: string,
    public readonly originalHtml: string,
    public readonly partialMarkdown: string,
    public override readonly cause?: Error
  ) {
    super(message);
    this.name = 'ContentConversionError';
  }
}

export class BackupError extends Error {
  constructor(
    message: string,
    public readonly componentName: string,
    public readonly operation: 'create' | 'load' | 'delete'
  ) {
    super(message);
    this.name = 'BackupError';
  }
}
