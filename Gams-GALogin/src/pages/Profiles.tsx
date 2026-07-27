import React, { useState, useMemo, useRef } from 'react';
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
  AppWindow,
  LayoutGrid,
  FileText,
  Upload,
  Download,
  Activity,
  X,
  FileCode,
  Settings,
  Plus,
  Folders,
  FolderPlus,
  FolderOpen,
  FolderX,
  Tag
} from 'lucide-react';
import { EditProfileModal } from '../components/EditProfileModal';

export const Profiles: React.FC = () => {
  const {
    profiles,
    searchTerm,
    launchProfile,
    stopProfile,
    cloneProfile,
    deleteProfile,
    updateProfile,
    startGroup,
    stopGroup,
    exportProfile,
    importProfile,
    fetchProfileLogs,
    clearProfileLogs,
    profileResources,
    arrangeWindows,
    proxies,
    templates,
    customGroups,
    bulkCreateProfiles,
    bulkCloneProfiles,
    bulkAssignProxies,
    bulkRenameProfiles,
    addCustomGroup,
    deleteCustomGroup,
    bulkAssignGroup
  } = useStore();

  // Selection states
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Local state for editing profile
  const [editingProfile, setEditingProfile] = useState<BrowserProfile | null>(null);
  
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

  // Window Manager States
  const [layoutMode, setLayoutMode] = useState<string>('grid');
  
  // Log Modal States
  const [logModalId, setLogModalId] = useState<string | null>(null);
  const [logContent, setLogContent] = useState<string>('');
  const [loadingLogs, setLoadingLogs] = useState(false);

  // Hidden File Import Input Ref
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Bulk Create States
  const [isBulkCreateOpen, setIsBulkCreateOpen] = useState(false);
  const [bulkPrefix, setBulkPrefix] = useState('Profile Mới');
  const [bulkCount, setBulkCount] = useState(5);
  const [bulkStartIndex, setBulkStartIndex] = useState(1);
  const [bulkGroup, setBulkGroup] = useState('Facebook Ads');
  const [bulkTemplateId, setBulkTemplateId] = useState('none');
  const [bulkSelectedProxyIds, setBulkSelectedProxyIds] = useState<string[]>([]);
  const [isSubmittingBulk, setIsSubmittingBulk] = useState(false);

  // Bulk Rename States
  const [isBulkRenameOpen, setIsBulkRenameOpen] = useState(false);
  const [bulkRenamePrefix, setBulkRenamePrefix] = useState('Profile GALogin');
  const [bulkRenameStartIndex, setBulkRenameStartIndex] = useState(1);

  // Group Management States
  const [isGroupPanelOpen, setIsGroupPanelOpen] = useState(true);
  const [newGroupName, setNewGroupName] = useState('');
  const [isAddingGroup, setIsAddingGroup] = useState(false);
  const [confirmDeleteGroup, setConfirmDeleteGroup] = useState<string | null>(null);

  // Bulk Assign Group States
  const [isBulkGroupOpen, setIsBulkGroupOpen] = useState(false);
  const [bulkGroupTarget, setBulkGroupTarget] = useState('');

  const handleAddGroup = () => {
    const trimmed = newGroupName.trim();
    if (!trimmed) return;
    addCustomGroup(trimmed);
    setNewGroupName('');
    setIsAddingGroup(false);
  };

  const handleDeleteGroup = (group: string) => {
    deleteCustomGroup(group);
    if (groupFilter === group) setGroupFilter('all');
    setConfirmDeleteGroup(null);
  };

  const handleBulkAssignGroupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIds.length === 0 || !bulkGroupTarget) return;
    setIsSubmittingBulk(true);
    await bulkAssignGroup(selectedIds, bulkGroupTarget);
    setIsBulkGroupOpen(false);
    setSelectedIds([]);
    setIsSubmittingBulk(false);
  };

  const handleBulkClone = async () => {
    if (selectedIds.length === 0) return;
    setIsSubmittingBulk(true);
    await bulkCloneProfiles(selectedIds);
    setSelectedIds([]);
    setIsSubmittingBulk(false);
  };

  const handleBulkCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkPrefix.trim()) return;
    setIsSubmittingBulk(true);
    await bulkCreateProfiles({
      prefix: bulkPrefix,
      count: bulkCount,
      group: bulkGroup,
      templateId: bulkTemplateId !== 'none' ? bulkTemplateId : undefined,
      proxyIds: bulkSelectedProxyIds,
      startIndex: bulkStartIndex
    });
    setIsBulkCreateOpen(false);
    setIsSubmittingBulk(false);
    // Reset states
    setBulkPrefix('Profile Mới');
    setBulkCount(5);
    setBulkStartIndex(1);
    setBulkSelectedProxyIds([]);
  };

  const handleBulkRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIds.length === 0 || !bulkRenamePrefix.trim()) return;
    setIsSubmittingBulk(true);
    await bulkRenameProfiles(selectedIds, bulkRenamePrefix, bulkRenameStartIndex);
    setIsBulkRenameOpen(false);
    setSelectedIds([]);
    setIsSubmittingBulk(false);
  };

  const handleToggleBulkProxy = (proxyId: string) => {
    if (bulkSelectedProxyIds.includes(proxyId)) {
      setBulkSelectedProxyIds(bulkSelectedProxyIds.filter(id => id !== proxyId));
    } else {
      setBulkSelectedProxyIds([...bulkSelectedProxyIds, proxyId]);
    }
  };

  // Bulk Assign Proxy States
  const [isBulkProxyOpen, setIsBulkProxyOpen] = useState(false);
  const [bulkAssignProxyIds, setBulkAssignProxyIds] = useState<string[]>([]);
  const [bulkProxyMode, setBulkProxyMode] = useState<'single' | 'round-robin' | 'all-fallback'>('round-robin');

  const handleBulkAssignProxySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIds.length === 0) return;
    setIsSubmittingBulk(true);
    await bulkAssignProxies(selectedIds, bulkAssignProxyIds, bulkProxyMode);
    setIsBulkProxyOpen(false);
    setSelectedIds([]);
    setIsSubmittingBulk(false);
    setBulkAssignProxyIds([]);
  };

  const handleToggleAssignBulkProxy = (proxyId: string) => {
    if (bulkProxyMode === 'single') {
      setBulkAssignProxyIds([proxyId]);
    } else {
      if (bulkAssignProxyIds.includes(proxyId)) {
        setBulkAssignProxyIds(bulkAssignProxyIds.filter(id => id !== proxyId));
      } else {
        setBulkAssignProxyIds([...bulkAssignProxyIds, proxyId]);
      }
    }
  };

  // Extract unique groups for filters (merge customGroups + groups from profiles)
  const allGroupNames = useMemo(() => {
    const fromProfiles = profiles.map((p) => p.group).filter(Boolean);
    const combined = new Set([...customGroups, ...fromProfiles]);
    return Array.from(combined).sort();
  }, [profiles, customGroups]);

  // Per-group profile counts
  const groupCounts = useMemo(() => {
    const map: Record<string, number> = {};
    profiles.forEach((p) => {
      if (p.group) map[p.group] = (map[p.group] || 0) + 1;
    });
    return map;
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
          (p.proxy && p.proxy.toLowerCase().includes(term)) ||
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

  // Bulk actions with layout coordinates mapping
  const handleBulkLaunch = () => {
    selectedIds.forEach((id, index) => {
      const profile = profiles.find((p) => p.id === id);
      if (profile && profile.status === 'stopped') {
        launchProfile(id, {
          layoutMode,
          layoutIndex: index,
          layoutTotal: selectedIds.length,
          screenWidth: window.screen.width,
          screenHeight: window.screen.height
        });
      }
    });
    setSelectedIds([]);
  };

  const handleBulkStop = () => {
    selectedIds.forEach((id) => {
      const profile = profiles.find((p) => p.id === id);
      if (profile && (profile.status === 'running' || profile.status === 'starting')) {
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

  // Group operations
  const handleStartGroup = () => {
    if (groupFilter === 'all') {
      alert('Vui lòng chọn một nhóm cụ thể để khởi chạy.');
      return;
    }
    startGroup(groupFilter);
  };

  const handleStopGroup = () => {
    if (groupFilter === 'all') {
      alert('Vui lòng chọn một nhóm cụ thể để dừng.');
      return;
    }
    stopGroup(groupFilter);
  };

  // Backup Import Handler
  const handleImportBackup = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64 = event.target?.result?.toString().split(',')[1];
      if (base64) {
        await importProfile(base64);
      }
    };
    reader.readAsDataURL(file);
    e.target.value = ''; // Reset input
  };

  // Arrange open windows
  const handleArrangeWindows = () => {
    const runningIds = profiles.filter(p => p.status === 'running').map(p => p.id);
    if (runningIds.length === 0) {
      alert('Không có profile nào đang chạy để sắp xếp.');
      return;
    }
    arrangeWindows(runningIds, layoutMode);
  };

  // Log viewer
  const handleOpenLogs = async (id: string) => {
    setLogModalId(id);
    setLoadingLogs(true);
    const content = await fetchProfileLogs(id);
    setLogContent(content || '[System] No logs recorded.');
    setLoadingLogs(false);
  };

  const handleClearLogs = async () => {
    if (logModalId) {
      await clearProfileLogs(logModalId);
      setLogContent('[System] Logs cleared.');
    }
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
        <div className="flex gap-2">
          {/* Backup Buttons */}
          <input
            type="file"
            accept=".zip"
            ref={fileInputRef}
            onChange={handleImportBackup}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl border border-dark-border bg-slate-900/60 text-slate-300 hover:text-white transition-all cursor-pointer"
            title="Import Profile from ZIP"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Nạp ZIP Backup</span>
          </button>
          <button
            onClick={() => setIsBulkCreateOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple text-white hover:opacity-90 hover:scale-[1.01] active:scale-[0.99] transition-all cursor-pointer shadow-lg shadow-brand-blue/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Tạo hàng loạt</span>
          </button>
        </div>
      </div>

      {/* Main flex layout: Group Sidebar + Content */}
      <div className="flex gap-4 items-start">

        {/* ── LEFT: Group Sidebar Panel ── */}
        <div
          className={`shrink-0 transition-all duration-300 ${
            isGroupPanelOpen ? 'w-52' : 'w-12'
          }`}
        >
          <div className="rounded-2xl border border-dark-border bg-slate-900/20 overflow-hidden">
            {/* Panel Header */}
            <div className="flex items-center justify-between px-3 py-3 border-b border-dark-border">
              <button
                onClick={() => setIsGroupPanelOpen(!isGroupPanelOpen)}
                className="flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-white transition-colors cursor-pointer"
              >
                <Folders className="w-4 h-4 text-brand-purple shrink-0" />
                {isGroupPanelOpen && <span>Nhóm Profile</span>}
              </button>
              {isGroupPanelOpen && (
                <button
                  onClick={() => setIsAddingGroup(true)}
                  className="p-1 rounded-lg text-slate-500 hover:text-brand-blue hover:bg-brand-blue/10 transition-all cursor-pointer"
                  title="Tạo nhóm mới"
                >
                  <FolderPlus className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {isGroupPanelOpen && (
              <div className="py-2 space-y-0.5">
                {/* "Tất cả" filter */}
                <button
                  onClick={() => setGroupFilter('all')}
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs transition-all cursor-pointer ${
                    groupFilter === 'all'
                      ? 'text-white bg-brand-blue/10 border-l-2 border-brand-blue'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <AppWindow className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate font-medium">Tất cả</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{profiles.length}</span>
                </button>

                {/* Group items */}
                {allGroupNames.map((group) => (
                  <div key={group} className="group/item relative">
                    <button
                      onClick={() => setGroupFilter(groupFilter === group ? 'all' : group)}
                      className={`w-full flex items-center justify-between px-3 py-2 text-xs transition-all cursor-pointer pr-8 ${
                        groupFilter === group
                          ? 'text-white bg-brand-purple/10 border-l-2 border-brand-purple'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FolderOpen className={`w-3.5 h-3.5 shrink-0 ${
                          groupFilter === group ? 'text-brand-purple' : 'text-slate-500'
                        }`} />
                        <span className="truncate font-medium">{group}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">
                        {groupCounts[group] ?? 0}
                      </span>
                    </button>

                    {/* Delete Group Button */}
                    {confirmDeleteGroup === group ? (
                      <div className="absolute inset-y-0 right-1 flex items-center gap-1">
                        <button
                          onClick={() => handleDeleteGroup(group)}
                          className="text-[9px] px-1.5 py-0.5 rounded bg-brand-rose/20 text-brand-rose hover:bg-brand-rose/30 font-bold cursor-pointer"
                        >
                          Xóa!
                        </button>
                        <button
                          onClick={() => setConfirmDeleteGroup(null)}
                          className="text-[9px] text-slate-500 hover:text-white cursor-pointer"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteGroup(group)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover/item:opacity-100 p-1 rounded text-slate-600 hover:text-brand-rose transition-all cursor-pointer"
                        title="Xóa nhóm này"
                      >
                        <FolderX className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}

                {/* Add new group inline input */}
                {isAddingGroup ? (
                  <div className="px-2 py-2">
                    <input
                      autoFocus
                      type="text"
                      placeholder="Tên nhóm mới..."
                      value={newGroupName}
                      onChange={(e) => setNewGroupName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleAddGroup();
                        if (e.key === 'Escape') { setIsAddingGroup(false); setNewGroupName(''); }
                      }}
                      className="w-full px-2 py-1.5 rounded-lg border border-brand-blue/30 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-brand-blue"
                    />
                    <div className="flex gap-1 mt-1.5">
                      <button
                        onClick={handleAddGroup}
                        className="flex-1 py-1 rounded-lg bg-brand-blue/20 text-brand-blue text-[10px] font-semibold hover:bg-brand-blue/30 cursor-pointer transition-all"
                      >
                        Thêm
                      </button>
                      <button
                        onClick={() => { setIsAddingGroup(false); setNewGroupName(''); }}
                        className="py-1 px-2 rounded-lg bg-slate-800 text-slate-400 text-[10px] hover:text-white cursor-pointer transition-all"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setIsAddingGroup(true)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-600 hover:text-brand-blue hover:bg-brand-blue/5 transition-all cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Thêm nhóm...</span>
                  </button>
                )}

                {/* Group Start/Stop Actions */}
                {groupFilter !== 'all' && (
                  <div className="px-2 py-2 flex gap-1 border-t border-dark-border mt-1">
                    <button
                      onClick={handleStartGroup}
                      className="flex-1 py-1.5 rounded-lg border border-brand-blue bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/10 text-[10px] font-bold transition-all cursor-pointer"
                    >
                      ▶ Start
                    </button>
                    <button
                      onClick={handleStopGroup}
                      className="flex-1 py-1.5 rounded-lg border border-brand-rose bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 text-[10px] font-bold transition-all cursor-pointer"
                    >
                      ■ Stop
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/*    RIGHT: Main content (filters + table)    */}
        <div className="flex-1 min-w-0 space-y-4">

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

          {/* Filters & Groups Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Lọc:</span>
            </div>

            {/* Group Filter Dropdown (now secondary) */}
              <select
                value={groupFilter}
                onChange={(e) => setGroupFilter(e.target.value)}
                className="px-3 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900 cursor-pointer"
              >
                <option value="all">Nhóm: Tất cả</option>
                {allGroupNames.map((g) => (
                  <option key={g} value={g}>
                    Nhóm: {g}
                  </option>
                ))}
              </select>

            {/* Group Start/Stop Actions inline with filter (hidden - moved to sidebar) */}

            {/* Platform Filter */}
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900 cursor-pointer"
            >
              <option value="all">OS: Tất cả</option>
              <option value="Windows">Windows</option>
              <option value="macOS">macOS</option>
              <option value="Linux">Linux</option>
            </select>
          </div>

          {/* Window Layouts Controller */}
          <div className="flex items-center gap-2 border border-dark-border bg-slate-950/40 px-3 py-1.5 rounded-xl">
            <LayoutGrid className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={layoutMode}
              onChange={(e) => setLayoutMode(e.target.value)}
              className="bg-transparent text-xs text-slate-300 outline-none cursor-pointer"
            >
              <option value="grid">Layout: Auto Grid</option>
              <option value="cascade">Layout: Cascade</option>
              <option value="tile">Layout: Tile</option>
              <option value="vertical">Layout: Dọc (Vertical)</option>
              <option value="horizontal">Layout: Ngang (Horizontal)</option>
            </select>
            <button
              onClick={handleArrangeWindows}
              className="ml-2 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-[10px] font-bold text-white transition-all cursor-pointer"
            >
              Arrange
            </button>
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
                <span>Mở đồng loạt ({layoutMode})</span>
              </button>
              <button
                onClick={handleBulkStop}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dark-border bg-slate-900/60 text-slate-400 hover:text-white transition-all cursor-pointer"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Đóng đồng loạt</span>
              </button>
              <button
                onClick={handleBulkClone}
                disabled={isSubmittingBulk}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dark-border bg-slate-900/60 text-slate-300 hover:text-white transition-all cursor-pointer disabled:opacity-50"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Nhân bản đồng loạt</span>
              </button>
              <button
                onClick={() => setIsBulkProxyOpen(true)}
                disabled={isSubmittingBulk}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-blue/20 bg-brand-blue/10 text-brand-blue hover:bg-brand-blue/20 transition-all cursor-pointer disabled:opacity-50 font-semibold"
              >
                <Settings className="w-3.5 h-3.5" />
                <span>Gán Proxy đồng loạt</span>
              </button>
              <button
                onClick={() => setIsBulkRenameOpen(true)}
                disabled={isSubmittingBulk}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-blue/20 bg-brand-blue/10 text-brand-blue hover:bg-brand-blue/20 transition-all cursor-pointer disabled:opacity-50 font-semibold"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Sửa Tên đồng loạt</span>
              </button>
              <button
                onClick={() => {
                  setBulkGroupTarget(allGroupNames[0] || '');
                  setIsBulkGroupOpen(true);
                }}
                disabled={isSubmittingBulk}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-purple/20 bg-brand-purple/10 text-brand-purple hover:bg-brand-purple/20 transition-all cursor-pointer disabled:opacity-50 font-semibold"
              >
                <Tag className="w-3.5 h-3.5" />
                <span>Gán Nhóm đồng loạt</span>
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
                <th className="p-4">Tài nguyên (Real)</th>
                <th className="p-4 cursor-pointer hover:text-slate-300 transition-colors" onClick={() => handleSort('lastOpened')}>
                  <div className="flex items-center gap-1">
                    <span>Mở gần nhất</span>
                    {sortField === 'lastOpened' ? (sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />) : null}
                  </div>
                </th>
                <th className="p-4 max-w-xs">Ghi chú</th>
                <th className="p-4 text-right pr-6 w-60">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border text-xs">
              {processedProfiles.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-16 text-center text-slate-600 text-sm font-medium">
                    Không tìm thấy profile nào phù hợp. Thử thay đổi bộ lọc hoặc tạo profile mới.
                  </td>
                </tr>
              ) : (
                processedProfiles.map((p) => {
                  const isSelected = selectedIds.includes(p.id);
                  const isRunning = p.status === 'running';
                  const isStarting = p.status === 'starting';
                  const isError = p.status === 'error';

                  // Real Resource Stats lookup
                  const stats = profileResources[p.id];
                  
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
                        ) : isStarting ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-bold bg-brand-blue/10 text-brand-blue border border-brand-blue/20 animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-blue"></span>
                            Starting...
                          </span>
                        ) : isError ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-bold bg-brand-rose/10 text-brand-rose border border-brand-rose/20">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-rose"></span>
                            Error
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xxs font-bold bg-slate-900 text-slate-500 border border-dark-border">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
                            Đã dừng
                          </span>
                        )}
                      </td>

                      {/* Proxy */}
                      <td className="p-4 font-mono text-slate-400">
                        {p.proxy === 'Không dùng Proxy (Direct)' || p.proxy === 'No Proxy (Direct)' ? (
                          <span className="text-slate-600 font-sans">Không sử dụng</span>
                        ) : (
                          <div>
                            <span>{p.proxy}</span>
                            <span className="block text-[10px] text-brand-emerald mt-0.5">● Đã kết nối • 92ms</span>
                          </div>
                        )}
                      </td>

                      {/* Browser version */}
                      <td className="p-4">
                        <div className="flex items-center gap-2 text-slate-300">
                          <span className="text-xxs px-2 py-0.5 rounded-sm bg-slate-900 text-slate-500 font-mono">
                            {p.platform}
                          </span>
                          <span className="text-xxs font-medium text-slate-400">
                            {p.browserType ? p.browserType.toUpperCase() : 'Chromium'}
                          </span>
                        </div>
                      </td>

                      {/* Resource Stats */}
                      <td className="p-4 font-mono text-slate-400">
                        {isRunning && stats ? (
                          <div className="space-y-0.5 text-xxs flex flex-col">
                            <span className="text-slate-300">PID: {p.pid || '—'}</span>
                            <span className="text-brand-purple">CPU: {stats.cpu}%</span>
                            <span className="text-brand-blue">RAM: {(stats.ramBytes / 1024 / 1024).toFixed(0)} MB</span>
                          </div>
                        ) : isRunning ? (
                          <div className="flex items-center gap-1 text-slate-500 text-xxs animate-pulse">
                            <Activity className="w-3.5 h-3.5" />
                            <span>Scanning...</span>
                          </div>
                        ) : (
                          <span className="text-slate-600 font-sans">—</span>
                        )}
                      </td>

                      {/* Last opened */}
                      <td className="p-4 text-slate-400 font-mono">
                        {p.lastOpened}
                      </td>

                      {/* Notes */}
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

                      {/* Actions */}
                      <td className="p-4 text-right pr-6">
                        <div className="flex items-center justify-end gap-2">
                          
                          {/* Launch / Close */}
                          {isRunning || isStarting ? (
                            <button
                              onClick={() => stopProfile(p.id)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 text-xxs font-semibold transition-all cursor-pointer"
                            >
                              <Square className="w-3 h-3" />
                              <span>Đóng</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => launchProfile(p.id, {
                                layoutMode,
                                layoutIndex: 0,
                                layoutTotal: 1,
                                screenWidth: window.screen.width,
                                screenHeight: window.screen.height
                              })}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-brand-blue/20 bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/15 text-xxs font-semibold transition-all cursor-pointer"
                            >
                              <Play className="w-3 h-3 fill-brand-blue/10" />
                              <span>Mở</span>
                            </button>
                          )}

                          {/* Edit Config Button */}
                          <button
                            onClick={() => setEditingProfile(p)}
                            title="Hiệu chỉnh cấu hình"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-slate-300 hover:border-slate-800 transition-all cursor-pointer"
                          >
                            <Settings className="w-3.5 h-3.5" />
                          </button>

                          {/* Options Dropdown menu trigger (Copy, Logs, Export Backup, Delete) */}
                          <button
                            onClick={() => handleOpenLogs(p.id)}
                            title="Xem Logs Profile"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-slate-300 hover:border-slate-800 transition-all cursor-pointer"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => exportProfile(p.id)}
                            title="Export Backup ZIP"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-slate-300 hover:border-slate-800 transition-all cursor-pointer"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => cloneProfile(p.id)}
                            title="Clone Profile"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-slate-300 hover:border-slate-800 transition-all cursor-pointer"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>

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
          <span>Phím tắt: F5 Làm mới • Sắp xếp màn hình giúp kiểm soát nhiều luồng trình duyệt</span>
        </div>
      </div>

        </div>{/* end right flex col */}
      </div>{/* end flex layout */}

      {/* Profile Logs Modal Dialog */}
      {logModalId && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-3xl rounded-2xl border border-dark-border bg-dark-card p-6 shadow-2xl space-y-4">
            
            <div className="flex justify-between items-center border-b border-dark-border pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-brand-purple" />
                <h3 className="text-sm font-bold text-slate-200">
                  Nhật Ký Tiến Trình: Profile ID {logModalId}
                </h3>
              </div>
              <button 
                onClick={() => setLogModalId(null)}
                className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white transition-all cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-dark-border h-[400px] overflow-y-auto font-mono text-xxs text-slate-400 space-y-1.5 select-text selection:bg-brand-blue/30 scrollbar-thin">
              {loadingLogs ? (
                <div className="flex items-center justify-center h-full text-slate-500">
                  <span>Đang nạp dữ liệu log từ máy chủ...</span>
                </div>
              ) : (
                logContent.split('\n').map((line, idx) => (
                  <div key={idx} className={
                    line.includes('[ERROR]') ? 'text-brand-rose' :
                    line.includes('[SUCCESS]') ? 'text-brand-emerald' :
                    line.includes('[WARNING]') ? 'text-amber-500' : 'text-slate-400'
                  }>
                    {line}
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-between items-center pt-2">
              <button
                type="button"
                onClick={handleClearLogs}
                className="px-3.5 py-2 rounded-xl border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 text-xs font-semibold transition-all cursor-pointer"
              >
                Dọn sạch Logs
              </button>
              <button
                type="button"
                onClick={() => setLogModalId(null)}
                className="px-5 py-2.5 rounded-xl bg-slate-900 border border-dark-border text-slate-300 hover:text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Đóng
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Edit Profile Modal Dialog */}
      <EditProfileModal
        profile={editingProfile}
        onClose={() => setEditingProfile(null)}
      />

      {/* Bulk Create Profile Modal Dialog */}
      {isBulkCreateOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
            <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none"></div>

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-200">Tạo Hàng Loạt Profiles</h3>
                <p className="text-xs text-slate-500">Tạo nhanh số lượng lớn trình duyệt và tự động gán Proxy tuần tự.</p>
              </div>
              <button
                onClick={() => setIsBulkCreateOpen(false)}
                className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleBulkCreateSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 block">Prefix tên Profile <span className="text-brand-rose">*</span></label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: GALogin Profile"
                  value={bulkPrefix}
                  onChange={(e) => setBulkPrefix(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950 focus:outline-none"
                />
                 <span className="text-[10px] text-slate-500">
                  Sẽ tạo ra dạng: {bulkPrefix} {String(bulkStartIndex).padStart(3, '0')}, {bulkPrefix} {String(bulkStartIndex + 1).padStart(3, '0')}...
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 block">Số lượng <span className="text-brand-rose">*</span></label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={100}
                    value={bulkCount}
                    onChange={(e) => setBulkCount(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 block">Bắt đầu từ số <span className="text-brand-rose">*</span></label>
                  <input
                    type="number"
                    required
                    min={0}
                    value={bulkStartIndex}
                    onChange={(e) => setBulkStartIndex(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 block">Nhóm gắn thẻ</label>
                  <input
                    type="text"
                    value={bulkGroup}
                    onChange={(e) => setBulkGroup(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950"
                  />
                </div>
              </div>

              {templates.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 block">Sử dụng Template cấu hình</label>
                  <select
                    value={bulkTemplateId}
                    onChange={(e) => setBulkTemplateId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-dark-border rounded-xl text-xs text-slate-300 focus:outline-none cursor-pointer"
                  >
                    <option value="none">Không sử dụng (Mặc định Chromium)</option>
                    {templates.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Proxies Selection */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-400">Gán danh sách Proxy tuần tự ({bulkSelectedProxyIds.length} đã chọn)</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setBulkSelectedProxyIds(proxies.map(p => p.id))}
                      className="text-[10px] text-brand-blue hover:underline font-semibold"
                    >
                      Chọn tất cả
                    </button>
                    <span className="text-[10px] text-slate-600">|</span>
                    <button
                      type="button"
                      onClick={() => setBulkSelectedProxyIds([])}
                      className="text-[10px] text-slate-500 hover:underline font-semibold"
                    >
                      Bỏ chọn
                    </button>
                  </div>
                </div>

                <div className="max-h-40 overflow-y-auto border border-dark-border rounded-xl bg-slate-950/40 p-2 space-y-1.5 scrollbar-thin">
                  {proxies.length === 0 ? (
                    <p className="text-xxs text-slate-600 text-center py-4">Chưa có proxy nào trong danh sách. Bấm vào Quản lý Proxy để nhập thêm.</p>
                  ) : (
                    proxies.map((pr) => {
                      const isChecked = bulkSelectedProxyIds.includes(pr.id);
                      return (
                        <label
                          key={pr.id}
                          className={`flex items-center justify-between p-2 rounded-lg border text-xxs cursor-pointer transition-all ${
                            isChecked ? 'border-brand-blue/30 bg-brand-blue/5 text-slate-200' : 'border-dark-border bg-slate-900/10 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => handleToggleBulkProxy(pr.id)}
                              className="rounded text-brand-blue"
                            />
                            <span className="font-mono">{pr.host}:{pr.port} ({pr.type})</span>
                          </div>
                          <span className="font-semibold text-slate-500 truncate max-w-[150px]">{pr.group}</span>
                        </label>
                      );
                    })
                  )}
                </div>
                <span className="text-[10px] text-slate-500 block leading-relaxed">
                  💡 *Hệ thống sẽ gán proxy xoay vòng lần lượt cho từng profile được tạo (Profile 1 gán Proxy 1, Profile 2 gán Proxy 2...).
                </span>
              </div>

              {/* Submit / Cancel Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-dark-border mt-5">
                <button
                  type="button"
                  onClick={() => setIsBulkCreateOpen(false)}
                  className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white hover:bg-slate-800/40 text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingBulk || !bulkPrefix.trim()}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingBulk ? (
                    <>
                      <Activity className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang xử lý tạo...</span>
                    </>
                  ) : (
                    <span>Tạo ngay {bulkCount} Profiles</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Bulk Assign Proxy Modal Dialog */}
      {isBulkProxyOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
            <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none"></div>

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-200">Gán Proxy Đồng Loạt</h3>
                <p className="text-xs text-slate-500">Đang chọn {selectedIds.length} profiles để gán proxy.</p>
              </div>
              <button
                onClick={() => setIsBulkProxyOpen(false)}
                className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleBulkAssignProxySubmit} className="space-y-4">
              
              {/* Assignment Mode */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 block">Chế độ gán proxy</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setBulkProxyMode('single');
                      setBulkAssignProxyIds([]);
                    }}
                    className={`py-2 rounded-xl text-xxs font-semibold border transition-all cursor-pointer ${
                      bulkProxyMode === 'single'
                        ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                        : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white'
                    }`}
                  >
                    1 Proxy cho tất cả
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setBulkProxyMode('round-robin');
                      setBulkAssignProxyIds([]);
                    }}
                    className={`py-2 rounded-xl text-xxs font-semibold border transition-all cursor-pointer ${
                      bulkProxyMode === 'round-robin'
                        ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                        : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white'
                    }`}
                  >
                    Gán tuần tự (vòng tròn)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setBulkProxyMode('all-fallback');
                      setBulkAssignProxyIds([]);
                    }}
                    className={`py-2 rounded-xl text-xxs font-semibold border transition-all cursor-pointer ${
                      bulkProxyMode === 'all-fallback'
                        ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                        : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white'
                    }`}
                  >
                    Gán dạng Dự phòng
                  </button>
                </div>
              </div>

              {/* Proxies Selection */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-400">
                    {bulkProxyMode === 'single' 
                      ? 'Chọn 1 Proxy' 
                      : bulkProxyMode === 'all-fallback'
                      ? `Chọn danh sách Proxy dự phòng (${bulkAssignProxyIds.length} đã chọn)`
                      : `Chọn các Proxy để xoay vòng (${bulkAssignProxyIds.length} đã chọn)`
                    }
                  </label>
                  {(bulkProxyMode === 'round-robin' || bulkProxyMode === 'all-fallback') && (
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setBulkAssignProxyIds(proxies.map(p => p.id))}
                        className="text-[10px] text-brand-blue hover:underline font-semibold"
                      >
                        Chọn tất cả
                      </button>
                      <span className="text-[10px] text-slate-600">|</span>
                      <button
                        type="button"
                        onClick={() => setBulkAssignProxyIds([])}
                        className="text-[10px] text-slate-500 hover:underline font-semibold"
                      >
                        Bỏ chọn
                      </button>
                    </div>
                  )}
                </div>

                <div className="max-h-48 overflow-y-auto border border-dark-border rounded-xl bg-slate-950/40 p-2 space-y-1.5 scrollbar-thin">
                  {proxies.length === 0 ? (
                    <p className="text-xxs text-slate-600 text-center py-4">Chưa có proxy nào. Hãy cấu hình proxy trước.</p>
                  ) : (
                    proxies.map((pr) => {
                      const isChecked = bulkAssignProxyIds.includes(pr.id);
                      return (
                        <label
                          key={pr.id}
                          className={`flex items-center justify-between p-2 rounded-lg border text-xxs cursor-pointer transition-all ${
                            isChecked ? 'border-brand-blue/30 bg-brand-blue/5 text-slate-200' : 'border-dark-border bg-slate-900/10 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <input
                              type={bulkProxyMode === 'single' ? 'radio' : 'checkbox'}
                              name="bulk_assign_proxy"
                              checked={isChecked}
                              onChange={() => handleToggleAssignBulkProxy(pr.id)}
                              className="rounded text-brand-blue"
                            />
                            <span className="font-mono">{pr.host}:{pr.port} ({pr.type})</span>
                          </div>
                          <span className="font-semibold text-slate-500 truncate max-w-[150px]">{pr.group}</span>
                        </label>
                      );
                    })
                  )}
                </div>
                <span className="text-[10px] text-slate-500 block leading-relaxed">
                  {bulkProxyMode === 'single' 
                    ? '💡 Tất cả profile được chọn sẽ dùng chung proxy này.' 
                    : bulkProxyMode === 'all-fallback'
                    ? '💡 Gán cả danh sách proxy dự phòng cho mỗi profile. Khi chạy, hệ thống sẽ tự động check live từng proxy cho đến khi tìm được proxy sống để mở trình duyệt, giúp tránh lỗi proxy die đột ngột!'
                    : '💡 Các proxy được chọn sẽ được phân phối tuần tự xoay vòng lần lượt cho các profile đã chọn.'
                  }
                </span>
              </div>

              {/* Submit / Cancel Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-dark-border mt-5">
                <button
                  type="button"
                  onClick={() => setIsBulkProxyOpen(false)}
                  className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white hover:bg-slate-800/40 text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingBulk || bulkAssignProxyIds.length === 0}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingBulk ? (
                    <>
                      <Activity className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang xử lý gán...</span>
                    </>
                  ) : (
                    <span>Xác nhận gán Proxy</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* Bulk Rename Profile Modal Dialog */}
      {isBulkRenameOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-md rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
            <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-purple/10 rounded-full blur-3xl pointer-events-none"></div>

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-200">Đổi Tên Đồng Loạt</h3>
                <p className="text-xs text-slate-500">Đang đổi tên cho {selectedIds.length} profiles.</p>
              </div>
              <button
                onClick={() => setIsBulkRenameOpen(false)}
                className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleBulkRenameSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 block">Prefix tên Profile mới <span className="text-brand-rose">*</span></label>
                <input
                  type="text"
                  required
                  placeholder="Ví dụ: GALogin FB Clone"
                  value={bulkRenamePrefix}
                  onChange={(e) => setBulkRenamePrefix(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950 focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 block">Bắt đầu đánh số từ <span className="text-brand-rose">*</span></label>
                <input
                  type="number"
                  required
                  min={0}
                  value={bulkRenameStartIndex}
                  onChange={(e) => setBulkRenameStartIndex(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950 focus:outline-none"
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Preview: {bulkRenamePrefix} {String(bulkRenameStartIndex).padStart(3, '0')}, {bulkRenamePrefix} {String(bulkRenameStartIndex + 1).padStart(3, '0')}...
                </span>
              </div>

              {/* Submit / Cancel Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-dark-border mt-5">
                <button
                  type="button"
                  onClick={() => setIsBulkRenameOpen(false)}
                  className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white hover:bg-slate-800/40 text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingBulk || !bulkRenamePrefix.trim()}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingBulk ? (
                    <>
                      <Activity className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang đổi tên...</span>
                    </>
                  ) : (
                    <span>Xác nhận đổi tên</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Assign Group Modal Dialog */}
      {isBulkGroupOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-md rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
            <div className="absolute -top-12 -left-12 w-48 h-48 bg-brand-purple/10 rounded-full blur-3xl pointer-events-none"></div>

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                  <Tag className="w-5 h-5 text-brand-purple" />
                  Gán Nhóm Đồng Loạt
                </h3>
                <p className="text-xs text-slate-500">Đang gán nhóm cho {selectedIds.length} profiles đã chọn.</p>
              </div>
              <button
                onClick={() => setIsBulkGroupOpen(false)}
                className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleBulkAssignGroupSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Chọn Nhóm cần gán <span className="text-brand-rose">*</span></label>

                {/* Existing groups as clickable chips */}
                <div className="flex flex-wrap gap-2">
                  {allGroupNames.map((group) => (
                    <button
                      key={group}
                      type="button"
                      onClick={() => setBulkGroupTarget(group)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                        bulkGroupTarget === group
                          ? 'bg-brand-purple/20 border-brand-purple/40 text-brand-purple shadow-md shadow-brand-purple/10'
                          : 'bg-slate-900/40 border-dark-border text-slate-400 hover:text-white hover:border-slate-700'
                      }`}
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                      {group}
                      <span className="text-[10px] font-mono text-slate-500 ml-1">({groupCounts[group] ?? 0})</span>
                    </button>
                  ))}
                </div>

                {/* Or type a new group name */}
                <div className="mt-3 pt-3 border-t border-dark-border">
                  <label className="text-xs text-slate-500 block mb-1.5">Hoặc nhập tên nhóm mới:</label>
                  <input
                    type="text"
                    placeholder="Nhập tên nhóm..."
                    value={bulkGroupTarget}
                    onChange={(e) => setBulkGroupTarget(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 focus:bg-slate-950 focus:outline-none focus:border-brand-purple/40"
                  />
                </div>

                {bulkGroupTarget && (
                  <p className="text-[10px] text-slate-500">
                    💡 Sẽ gán nhóm <span className="text-brand-purple font-semibold">"{bulkGroupTarget}"</span> cho {selectedIds.length} profiles.
                    {!allGroupNames.includes(bulkGroupTarget) && (
                      <span className="text-brand-blue ml-1">(Nhóm mới sẽ được tạo tự động)</span>
                    )}
                  </p>
                )}
              </div>

              {/* Submit / Cancel Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-dark-border mt-5">
                <button
                  type="button"
                  onClick={() => setIsBulkGroupOpen(false)}
                  className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white hover:bg-slate-800/40 text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingBulk || !bulkGroupTarget.trim()}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-brand-purple to-brand-blue hover:opacity-90 text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmittingBulk ? (
                    <>
                      <Activity className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang gán nhóm...</span>
                    </>
                  ) : (
                    <span>Xác nhận gán Nhóm</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
