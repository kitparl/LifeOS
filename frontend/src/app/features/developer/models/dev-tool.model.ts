export interface DevToolCategory {
  id: string;
  label: string;
  description: string;
  icon: string;
}

export interface DevToolMeta {
  id: string;
  name: string;
  description: string;
  /** Route segment under the Developer mount, e.g. 'base64' -> /developer/base64 or /explore/developer/base64 */
  route: string;
  icon: string;
  /** A tool can appear under more than one category (PRD lists some tools twice). */
  categories: string[];
  keywords: string[];
}
