import React, { useState, useMemo } from 'react';
import { useStore } from '../store/useStore';
import type { BrowserProfile } from '../store/useStore';
import {
  Play,
  Square,
  Copy,
  Trash2,
  Edit2,
  ChevronDown,
  CheckSquare,
  Square as SquareOutline,
  SlidersHorizontal,
  ChevronUp,
  AppWindow
} from 'lucide-react';

export const Profiles: React.FC = () => {
  const {
    profiles,
    searchTerm,
    launchProfile,
    stopProfile,
    cloneProfile,
    deleteProfile,
    updateProfile
  } = useStore();

  // Selection states
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Filtering states
  const [statusFilter, setStatusFilter] = useState<'all' | 'running' | 'stopped'>('all');
  const [groupFilter, setGroupFilter] = useState('all');
  const [platformFilter, setPlatformFilter] = useState('all');

  // Sorting states
  const [sortField, setSortField] = useState<keyof BrowserProfile>('name');
  const [sortAsc, setSortAsc] = useState(true);

  // Edit notes overlay state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingNotes, setEditingNotes] = useState('');

  // Extract unique groups for filters
  const groups = useMemo(() => {
    const set = new Set(profiles.map((p) => p.group));
    return ['all', ...Array.from(set)];
  }, [profiles]);

  // Handle individual header sort triggers
  const handleSort = (field: keyof BrowserProfile) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  // Filtered & Sorted Profiles
  const processedProfiles = useMemo(() => {
    let list = [...profiles];

    // Search term matching
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(term) ||
          p.proxy.toLowerCase().includes(term) ||
          p.notes.toLowerCase().includes(term) ||
          p.group.toLowerCase().includes(term)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      list = list.filter((p) => p.status === statusFilter);
    }

    // Group filter
    if (groupFilter !== 'all') {
      list = list.filter((p) => p.group === groupFilter);
    }

    // Platform filter
    if (platformFilter !== 'all') {
      list = list.filter((p) => p.platform === platformFilter);
    }

    // Sort order
    list.sort((a, b) => {
      let aVal = a[sortField] ?? '';
      let bVal = b[sortField] ?? '';

      // Convert to string for easy comparison
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();

      if (aVal < bVal) return sortAsc ? -1 : 1;
      if (aVal > bVal) return sortAsc ? 1 : -1;
      return 0;
    });

    return list;
  }, [profiles, searchTerm, statusFilter, groupFilter, platformFilter, sortField, sortAsc]);

  // Selection handlers
  const handleSelectAll = () => {
    if (selectedIds.length === processedProfiles.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(processedProfiles.map((p) => p.id));
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  // Bulk actions
  const handleBulkLaunch = () => {
    selectedIds.forEach((id) => {
      const profile = profiles.find((p) => p.id === id);
      if (profile && profile.status === 'stopped') {
        launchProfile(id);
      }
    });
    setSelectedIds([]);
  };

  const handleBulkStop = () => {
    selectedIds.forEach((id) => {
      const profile = profiles.find((p) => p.id === id);
      if (profile && profile.status === 'running') {
        stopProfile(id);
      }
    });
    setSelectedIds([]);
  };

  const handleBulkDelete = () => {
    if (confirm(`Bạn có chắc chắn muốn xóa ${selectedIds.length} profile đã chọn?`)) {
      selectedIds.forEach((id) => deleteProfile(id));
      setSelectedIds([]);
    }
  };

  const startEditNotes = (id: string, currentNotes: string) => {
    setEditingId(id);
    setEditingNotes(currentNotes);
  };

  const saveNotes = (id: string) => {
    updateProfile(id, { notes: editingNotes });
    setEditingId(null);
  };

  return (
    <div className="space-y-6 animate-fade-in relative min-h-[500px]">
      
      {/* Header and Counters */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Quản Lý Browser Profiles</h2>
          <p className="text-xs text-slate-500">
            Tổng cộng: <span className="font-semibold text-slate-400">{profiles.length}</span> | Đang chạy:{' '}
            <span className="font-semibold text-brand-emerald">{profiles.filter((p) => p.status === 'running').length}</span>
          </p>
        </div>
      </div>

      {/* Control / Filter Bar */}
      <div className="p-4 rounded-2xl border border-dark-border bg-slate-900/10 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          
          {/* Status Buttons */}
          <div className="flex rounded-xl border border-dark-border bg-slate-950/40 p-1">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                statusFilter === 'all'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Tất cả
            </button>
            <button
              onClick={() => setStatusFilter('running')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                statusFilter === 'running'
                  ? 'bg-brand-blue/10 text-brand-blue border border-brand-blue/20'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Đang hoạt động
            </button>
            <button
              onClick={() => setStatusFilter('stopped')}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                statusFilter === 'stopped'
                  ? 'bg-slate-900 text-slate-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Đã dừng
            </button>
          </div>

          {/* Filters Selectors */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Lọc:</span>
            </div>

            {/* Group Filter */}
            <select
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900 cursor-pointer"
            >
              <option value="all">Nhóm: Tất cả</option>
              {groups.filter((g) => g !== 'all').map((g) => (
                <option key={g} value={g}>
                  Nhóm: {g}
                </option>
              ))}
            </select>

            {/* Platform Filter */}
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900 cursor-pointer"
            >
              <option value="all">Hệ điều hành: Tất cả</option>
              <option value="Windows">Windows</option>
              <option value="macOS">macOS</option>
              <option value="Linux">Linux</option>
            </select>
          </div>

        </div>

        {/* Selection / Bulk Actions Row */}
        {selectedIds.length > 0 && (
          <div className="flex items-center justify-between p-3 rounded-xl border border-brand-blue/20 bg-brand-blue/5 animate-fade-in text-xs">
            <span className="font-semibold text-slate-300">
              Đã chọn <span className="text-brand-blue font-bold font-mono">{selectedIds.length}</span> profiles
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={handleBulkLaunch}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-blue hover:bg-brand-blue-hover text-white font-semibold transition-all cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Mở đồng loạt</span>
              </button>
              <button
                onClick={handleBulkStop}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dark-border bg-slate-900/60 text-slate-400 hover:text-white transition-all cursor-pointer"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Đóng đồng loạt</span>
              </button>
              <button
                onClick={handleBulkDelete}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 transition-all cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Xóa đồng loạt</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Profiles Data Grid */}
      <div className="border border-dark-border rounded-2xl bg-slate-950/30 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border bg-slate-900/20 text-xxs font-bold uppercase tracking-wider text-slate-500">
                <th className="p-4 w-12 text-center">
                  <button
                    onClick={handleSelectAll}
                    className="text-slate-500 hover:text-white transition-colors cursor-pointer"
                  >
                    {selectedIds.length === processedProfiles.length && processedProfiles.length > 0 ? (
                      <CheckSquare className="w-4.5 h-4.5 text-brand-blue" />
                    ) : (
                      <SquareOutline className="w-4.5 h-4.5" />
                    )}
                  </button>
                </th>
                <th className="p-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('name')}>
                  <div className="flex items-center gap-1">
                    <span>Tên Profile</span>
                    {sortField === 'name' ? (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />) : null}
                  </div>
                </th>
                <th className="p-4 text-center">Trạng Thái</th>
                <th className="p-4">Địa chỉ Proxy</th>
                <th className="p-4">Trình Duyệt</th>
                <th className="p-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('lastOpened')}>
                  <div className="flex items-center gap-1">
                    <span>Mở gần nhất</span>
                    {sortField === 'lastOpened' ? (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />) : null}
                  </div>
                </th>
                <th className="p-4 max-w-xs">Ghi chú</th>
                <th className="p-4 text-right pr-6 w-52">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border text-xs">
              {processedProfiles.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-16 text-center text-slate-600 text-sm font-medium">
                    Không tìm thấy profile nào phù hợp. Thử thay đổi bộ lọc hoặc tạo profile mới.
                  </td>
                </tr>
              ) : (
                processedProfiles.map((p) => {
                  const isSelected = selectedIds.includes(p.id);
                  const isRunning = p.status === 'running';
                  return (
                    <tr
                      key={p.id}
                      className={`hover:bg-slate-900/20 transition-all ${
                        isSelected ? 'bg-brand-blue/3 border-l-2 border-brand-blue' : ''
                      }`}
                    >
                      {/* Checkbox */}
                      <td className="p-4 text-center">
                        <button
                          onClick={() => handleSelectOne(p.id)}
                          className="text-slate-500 hover:text-slate-200 transition-colors cursor-pointer"
                        >
                          {isSelected ? (
                            <CheckSquare className="w-4.5 h-4.5 text-brand-blue" />
                          ) : (
                            <SquareOutline className="w-4.5 h-4.5" />
                          )}
                        </button>
                      </td>

                      {/* Profile Name & Group badge */}
                      <td className="p-4 font-semibold text-slate-200">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-slate-900/50 border border-dark-border text-slate-400">
                            <AppWindow className="w-4 h-4 text-brand-purple" />
                          </div>
                          <div>
                            <span className="block">{p.name}</span>
                            <span className="text-xxs font-semibold text-slate-500 mt-0.5 px-2 py-0.5 rounded-md bg-slate-900 border border-dark-border inline-block">
                              {p.group}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Status indicator */}
                      <td className="p-4 text-center">
                        {isRunning ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-bold bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/20 animate-pulse-slow">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-emerald"></span>
                            Đang chạy
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-bold bg-slate-900 text-slate-500 border border-dark-border">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
                            Đã dừng
                          </span>
                        )}
                      </td>

                      {/* Proxy string & status */}
                      <td className="p-4 font-mono text-slate-400">
                        {p.proxy === 'Không dùng Proxy (Direct)' || p.proxy === 'No Proxy (Direct)' ? (
                          <span className="text-slate-600 font-sans">Không sử dụng</span>
                        ) : (
                          <div>
                            <span>{p.proxy}</span>
                            {/* Latency sub-text simulator */}
                            <span className="block text-[10px] text-brand-emerald mt-0.5">● Đã kết nối • Độ trễ: 92ms</span>
                          </div>
                        )}
                      </td>

                      {/* Browser version & platform */}
                      <td className="p-4">
                        <div className="flex items-center gap-2 text-slate-300">
                          <span className="text-xxs px-2 py-0.5 rounded-sm bg-slate-900 text-slate-500 font-mono">
                            {p.platform}
                          </span>
                          <span className="text-xxs font-medium text-slate-400">
                            {p.browserVersion}
                          </span>
                        </div>
                      </td>

                      {/* Last opened */}
                      <td className="p-4 text-slate-400 font-mono">
                        {p.lastOpened}
                      </td>

                      {/* Notes text and inline editing */}
                      <td className="p-4 text-slate-500 max-w-xs truncate relative group">
                        {editingId === p.id ? (
                          <div className="flex items-center gap-1.5 z-10 relative">
                            <input
                              type="text"
                              value={editingNotes}
                              onChange={(e) => setEditingNotes(e.target.value)}
                              className="px-2 py-1 bg-slate-900 border border-brand-blue rounded text-xxs text-slate-200"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') saveNotes(p.id);
                                if (e.key === 'Escape') setEditingId(null);
                              }}
                              autoFocus
                            />
                            <button
                              onClick={() => saveNotes(p.id)}
                              className="px-1.5 py-0.5 bg-brand-blue text-white rounded text-[10px] font-bold"
                            >
                              Lưu
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate block flex-1">{p.notes || '—'}</span>
                            <button
                              onClick={() => startEditNotes(p.id, p.notes)}
                              className="opacity-0 group-hover:opacity-100 p-1 text-slate-600 hover:text-slate-300 transition-opacity cursor-pointer"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </td>

                      {/* Individual Profile actions */}
                      <td className="p-4 text-right pr-6">
                        <div className="flex items-center justify-end gap-2.5">
                          {/* Launch/Stop Toggle */}
                          {isRunning ? (
                            <button
                              onClick={() => stopProfile(p.id)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 text-xxs font-semibold transition-all cursor-pointer"
                            >
                              <Square className="w-3 h-3" />
                              <span>Đóng</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => launchProfile(p.id)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-brand-blue/20 bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/15 text-xxs font-semibold transition-all cursor-pointer"
                            >
                              <Play className="w-3 h-3 fill-brand-blue/10" />
                              <span>Mở</span>
                            </button>
                          )}

                          {/* Clone Button */}
                          <button
                            onClick={() => cloneProfile(p.id)}
                            title="Nhân bản profile"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-slate-300 hover:border-slate-800 transition-all cursor-pointer"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>

                          {/* Delete Button */}
                          <button
                            onClick={() => {
                              if (confirm(`Bạn chắc chắn muốn xóa profile "${p.name}"?`)) {
                                deleteProfile(p.id);
                              }
                            }}
                            title="Xóa profile"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-brand-rose hover:border-brand-rose/20 transition-all cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer info showing items count */}
        <div className="p-4 border-t border-dark-border bg-slate-900/10 flex items-center justify-between text-xxs text-slate-500">
          <span>Hiển thị {processedProfiles.length} trong tổng số {profiles.length} profiles</span>
          <span>Phím tắt: F5 Làm mới • Click đúp để mở nhanh profile</span>
        </div>

      </div>

    </div>
  );
};
