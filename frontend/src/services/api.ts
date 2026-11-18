import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

export interface SourceItemConfig {
  file_path: string;
  sheet_name?: string;
  header_row: number;
}

export interface InitDatasetRequest {
  session_id: string;
  sources: SourceItemConfig[];
  type_overrides?: Record<string, string>;
}

export interface CleaningActionRequest {
  session_id: string;
  action: string;
  params?: Record<string, any>;
}

export interface FilterCondition {
  column: string;
  operator: string;
  value?: any;
  value2?: any;
}

export interface ApplyFilterRequest {
  session_id: string;
  conditions: FilterCondition[];
  logic: 'AND' | 'OR';
}

export interface PivotRequest {
  session_id: string;
  rows?: string[];
  cols?: string[];
  values?: string[];
  agg_func?: string;
  filters?: FilterCondition[];
  sort_order?: 'asc' | 'desc';
}

export interface DrillDownRequest {
  session_id: string;
  row_filters: Record<string, any>;
  limit?: number;
}

// API methods
export const ApiService = {
  // Session
  createNewSession: async () => {
    const res = await api.post<{ session_id: string }>('/session/new');
    return res.data;
  },

  getSessionStatus: async (sessionId: string) => {
    const res = await api.get(`/session/${sessionId}/status`);
    return res.data;
  },

  // Step 1: Connect
  uploadFiles: async (sessionId: string, files: File[]) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    files.forEach((file) => formData.append('files', file));

    const res = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  initializeDataset: async (data: InitDatasetRequest) => {
    const res = await api.post('/dataset/initialize', data);
    return res.data;
  },

  // Step 2: Clean
  getCleaningProfile: async (sessionId: string) => {
    const res = await api.get(`/cleaning/profile?session_id=${sessionId}`);
    return res.data;
  },

  getCleaningPreview: async (sessionId: string, page = 1, limit = 25) => {
    const res = await api.get(`/cleaning/preview?session_id=${sessionId}&page=${page}&limit=${limit}`);
    return res.data;
  },

  executeCleaningAction: async (data: CleaningActionRequest) => {
    const res = await api.post('/cleaning/action', data);
    return res.data;
  },

  applyFilter: async (data: ApplyFilterRequest) => {
    const res = await api.post('/cleaning/filter', data);
    return res.data;
  },

  undoCleaning: async (sessionId: string) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    const res = await api.post('/cleaning/undo', formData);
    return res.data;
  },

  resetCleaning: async (sessionId: string) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    const res = await api.post('/cleaning/reset', formData);
    return res.data;
  },

  // Step 3: Analyze
  getAnalyzeOverview: async (sessionId: string) => {
    const res = await api.get(`/analyze/overview?session_id=${sessionId}`);
    return res.data;
  },

  getDistribution: async (sessionId: string, column: string, bins = 10) => {
    const res = await api.get(`/analyze/distribution?session_id=${sessionId}&column=${encodeURIComponent(column)}&bins=${bins}`);
    return res.data;
  },

  computePivot: async (data: PivotRequest) => {
    const res = await api.post('/analyze/pivot', data);
    return res.data;
  },

  drillDown: async (data: DrillDownRequest) => {
    const res = await api.post('/analyze/drilldown', data);
    return res.data;
  },

  // Step 4: Report
  generateReport: async (sessionId: string) => {
    const res = await api.get(`/report/generate?session_id=${sessionId}`);
    return res.data;
  },

  getExcelExportUrl: (sessionId: string) => `/api/report/export/excel?session_id=${sessionId}`,
  getPdfExportUrl: (sessionId: string) => `/api/report/export/pdf?session_id=${sessionId}`,
};

export default ApiService;
