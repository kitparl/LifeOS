export class PaginatedListState {
  readonly pageSize: number;
  currentPage = 1;
  total = 0;
  loading = false;

  constructor(pageSize = 25) {
    this.pageSize = pageSize;
  }

  get offset(): number {
    return (this.currentPage - 1) * this.pageSize;
  }

  setPage(page: number): void {
    this.currentPage = page;
  }
}
