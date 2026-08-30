let currentProfileEdit = "";

// Global Settings Toggle Logic
document.querySelectorAll('input[name="loop_type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        document.getElementById('loop_count').disabled = e.target.value !== 'n';
    });
});

document.querySelectorAll('input[name="delay_type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        document.getElementById('delay_fixed').disabled = e.target.value !== 'fixed';
        const isRandAll = e.target.value === 'random_all';
        document.getElementById('delay_rand_all_min').disabled = !isRandAll;
        document.getElementById('delay_rand_all_max').disabled = !isRandAll;
        const isRandInd = e.target.value === 'random_individual';
        document.getElementById('delay_rand_ind_min').disabled = !isRandInd;
        document.getElementById('delay_rand_ind_max').disabled = !isRandInd;
        document.getElementById('delay_times').disabled = e.target.value !== 'time';
    });
});

function getGlobalConfig() {
    return {
        loop_type: document.querySelector('input[name="loop_type"]:checked').value,
        loop_count: document.getElementById('loop_count').value,
        max_threads: document.getElementById('max_threads').value,
        delay_type: document.querySelector('input[name="delay_type"]:checked').value,
        delay_fixed: document.getElementById('delay_fixed').value,
        delay_rand_all_min: document.getElementById('delay_rand_all_min').value,
        delay_rand_all_max: document.getElementById('delay_rand_all_max').value,
        delay_rand_ind_min: document.getElementById('delay_rand_ind_min').value,
        delay_rand_ind_max: document.getElementById('delay_rand_ind_max').value,
        delay_times: document.getElementById('delay_times').value.split(',').map(s => s.trim()).filter(s => s),
        gpt_limit_action: document.querySelector('input[name="gpt_limit_action"]:checked').value,
        apply_gpt_limit_global: document.getElementById('apply_gpt_limit_global').checked,
        apply_fb_global: document.getElementById('apply_fb_global').checked,
        global_facebook_account: document.getElementById('global_facebook_account').value.trim(),
        only_scrape_no_post: document.getElementById('only_scrape_no_post').checked
    };
}

async function saveGlobalConfig() {
    const cfg = getGlobalConfig();
    try {
        const response = await fetch('/api/save_global_config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cfg)
        });
        const data = await response.json();
        alert(data.message);
    } catch (e) {
        console.error(e);
        alert("Lỗi khi lưu cài đặt!");
    }
}

async function loadGlobalConfig() {
    try {
        const response = await fetch('/api/global_config');
        const cfg = await response.json();
        if(!cfg) return;

        if (cfg.loop_type) {
            document.querySelector(`input[name="loop_type"][value="${cfg.loop_type}"]`).checked = true;
            document.getElementById('loop_count').disabled = cfg.loop_type !== 'n';
        }
        if (cfg.loop_count) document.getElementById('loop_count').value = cfg.loop_count;
        if (cfg.max_threads) document.getElementById('max_threads').value = cfg.max_threads;

        if (cfg.delay_type) {
            document.querySelector(`input[name="delay_type"][value="${cfg.delay_type}"]`).checked = true;
            document.getElementById('delay_fixed').disabled = cfg.delay_type !== 'fixed';
            const isRandAll = cfg.delay_type === 'random_all';
            document.getElementById('delay_rand_all_min').disabled = !isRandAll;
            document.getElementById('delay_rand_all_max').disabled = !isRandAll;
            const isRandInd = cfg.delay_type === 'random_individual';
            document.getElementById('delay_rand_ind_min').disabled = !isRandInd;
            document.getElementById('delay_rand_ind_max').disabled = !isRandInd;
            document.getElementById('delay_times').disabled = cfg.delay_type !== 'time';
        }
        if (cfg.delay_fixed) document.getElementById('delay_fixed').value = cfg.delay_fixed;
        if (cfg.delay_rand_all_min) document.getElementById('delay_rand_all_min').value = cfg.delay_rand_all_min;
        if (cfg.delay_rand_all_max) document.getElementById('delay_rand_all_max').value = cfg.delay_rand_all_max;
        if (cfg.delay_rand_ind_min) document.getElementById('delay_rand_ind_min').value = cfg.delay_rand_ind_min;
        if (cfg.delay_rand_ind_max) document.getElementById('delay_rand_ind_max').value = cfg.delay_rand_ind_max;
        if (cfg.delay_times) document.getElementById('delay_times').value = cfg.delay_times.join(', ');
        if (cfg.gpt_limit_action) {
            document.querySelector(`input[name="gpt_limit_action"][value="${cfg.gpt_limit_action}"]`).checked = true;
        }
        if (cfg.apply_gpt_limit_global !== undefined) {
            document.getElementById('apply_gpt_limit_global').checked = cfg.apply_gpt_limit_global;
        }
        if (cfg.apply_fb_global !== undefined) {
            document.getElementById('apply_fb_global').checked = cfg.apply_fb_global;
        }
        if (cfg.global_facebook_account !== undefined) {
            document.getElementById('global_facebook_account').value = cfg.global_facebook_account;
        }
        if (cfg.only_scrape_no_post !== undefined) {
            document.getElementById('only_scrape_no_post').checked = cfg.only_scrape_no_post === true || cfg.only_scrape_no_post === 'true';
        }

    } catch (e) {
        console.error("Lỗi khi tải cài đặt:", e);
    }
}

async function startAll() {
    const globalCfg = getGlobalConfig();
    try {
        const response = await fetch('/api/start_all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(globalCfg)
        });
        const data = await response.json();
        alert(data.message);
    } catch (e) {
        console.error(e);
    }
}

async function stopAll() {
    try {
        const response = await fetch('/api/stop_all', { method: 'POST' });
        const data = await response.json();
        alert(data.message);
    } catch (e) {
        console.error(e);
    }
}

async function forceStopTool() {
    if (!confirm("🚨 BẠN CÓ CHẮC CHẮN MUỐN DỪNG KHẨN CẤP KHÔNG?\nĐiều này sẽ TẮT HẲN SERVER và đóng tool!")) return;
    try {
        await fetch('/api/force_stop', { method: 'POST' });
        alert("Đã gửi lệnh tắt Server. Bạn có thể đóng trình duyệt.");
    } catch (e) {
        console.error(e);
    }
}

async function restartTool() {
    if (!confirm("🔄 Bạn có muốn KHỞI ĐỘNG LẠI Server Tool không? Mọi tiến trình sẽ bị ngắt!")) return;
    try {
        await fetch('/api/restart_tool', { method: 'POST' });
        alert("Đang khởi động lại Server. Vui lòng đợi 5 giây rồi F5 lại trang.");
        setTimeout(() => location.reload(), 5000);
    } catch (e) {
        console.error(e);
    }
}

async function startProfile(profile) {
    try {
        const response = await fetch(`/api/start/${encodeURIComponent(profile)}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) updateLog(profile, "Đang gửi lệnh Start...");
        else updateLog(profile, "Lỗi: " + data.message);
    } catch (e) { console.error(e); }
}

async function stopProfile(profile) {
    try {
        const response = await fetch(`/api/stop/${encodeURIComponent(profile)}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) updateLog(profile, "Đang gửi lệnh Stop...");
        else updateLog(profile, "Lỗi: " + data.message);
    } catch (e) { console.error(e); }
}

async function clearProfileLog(profile) {
    if (!confirm(`Bạn có chắc muốn xóa sạch log của ${profile} không?`)) return;
    try {
        const response = await fetch(`/api/clear_log/${encodeURIComponent(profile)}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            const logList = document.getElementById(`log-list-${profile}`);
            if (logList) logList.innerHTML = '<li>[Đã xóa sạch log]</li>';
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) { console.error(e); }
}

async function clearAllLogs() {
    if (!confirm("Bạn có chắc muốn xóa sạch log của TẤT CẢ profile không?")) return;
    try {
        const response = await fetch('/api/clear_all_logs', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            alert(data.message);
            location.reload();
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) { console.error(e); }
}

async function renameProfile(oldName) {
    const newName = prompt(`Nhập tên mới cho ${oldName}:`, oldName);
    if (!newName || newName === oldName) return;
    
    try {
        const response = await fetch(`/api/rename_profile/${encodeURIComponent(oldName)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName })
        });
        const data = await response.json();
        if (data.success) {
            alert("Đổi tên thành công!");
            location.reload();
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) {
        alert("Lỗi kết nối!");
    }
}

async function createProfile() {
    const newName = prompt("Nhập tên Profile mới (Ví dụ: Fanpage_A):");
    if (!newName) return;
    
    try {
        const response = await fetch('/api/create_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ profile_name: newName })
        });
        const data = await response.json();
        if (data.success) {
            alert("Đã tạo Profile thành công!");
            location.reload();
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) {
        alert("Lỗi kết nối!");
    }
}

async function deleteProfile(profileName) {
    if (!confirm(`🚨 BẠN CÓ CHẮC CHẮN MUỐN XÓA PROFILE "${profileName}" KHÔNG?\nHành động này sẽ gỡ Profile khỏi Dashboard.`)) return;
    
    try {
        const response = await fetch(`/api/delete_profile/${encodeURIComponent(profileName)}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert("Đã xóa Profile!");
            location.reload();
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) {
        alert("Lỗi kết nối!");
    }
}

async function openManualBrowser(profile) {
    try {
        const response = await fetch(`/api/manual_browser/${encodeURIComponent(profile)}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            alert(data.message);
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) {
        console.error(e);
        alert("Lỗi kết nối Server!");
    }
}

async function createOrSwitchGPTAccount(profile) {
    try {
        const response = await fetch(`/api/gpt_register/${encodeURIComponent(profile)}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            alert(data.message);
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (e) {
        console.error(e);
        alert("Lỗi kết nối Server!");
    }
}

// Modal Logic
function switchSettingsTab(tabId) {
    // Remove active class from all buttons and tab contents
    document.querySelectorAll('.modal-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to clicked button and target tab content
    const targetBtn = document.querySelector(`.modal-tab-btn[onclick*="${tabId}"]`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }
    const targetContent = document.getElementById(tabId);
    if (targetContent) {
        targetContent.classList.add('active');
    }
}

function getFacebookAssetId(url) {
    if (!url) return '';
    try {
        const u = new URL(url.trim());
        // Trích xuất asset_id từ query parameters
        let assetId = u.searchParams.get('asset_id');
        if (assetId) return assetId;
        
        // Trích xuất page_id từ query parameters
        let pageId = u.searchParams.get('page_id');
        if (pageId) return pageId;
        
        // Trích xuất id từ query parameters (ví dụ: profile.php?id=...)
        let idParam = u.searchParams.get('id');
        if (idParam) return idParam;
        
        // Dự phòng: Lấy phần cuối cùng của đường dẫn
        const segments = u.pathname.split('/').filter(s => s);
        if (segments.length > 0) {
            return segments[segments.length - 1];
        }
    } catch (e) {
        // Nếu không phải URL hợp lệ, trả về chính chuỗi đó sau khi trim
        return url.trim();
    }
    return url.trim();
}

function addFanpageInput(url = '') {
    const container = document.getElementById('fanpage-urls-container');
    if (!container) return;
    
    const row = document.createElement('div');
    row.className = 'fanpage-url-row';
    row.style.display = 'flex';
    row.style.gap = '0.5rem';
    row.style.alignItems = 'center';
    row.style.marginBottom = '0.5rem';
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'fanpage-url-input';
    input.value = url;
    input.placeholder = 'https://business.facebook.com/latest/composer/?asset_id=...';
    input.style.flex = '1';
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-stop';
    removeBtn.innerHTML = '🗑️';
    removeBtn.style.padding = '0.55rem';
    removeBtn.style.minWidth = '40px';
    removeBtn.style.flexShrink = '0';
    removeBtn.style.background = 'rgba(244, 63, 94, 0.1)';
    removeBtn.style.border = '1px solid rgba(244, 63, 94, 0.2)';
    removeBtn.style.color = '#fda4af';
    removeBtn.onclick = function() {
        row.remove();
    };
    
    row.appendChild(input);
    row.appendChild(removeBtn);
    container.appendChild(row);
}

async function openSettings(profile) {
    currentProfileEdit = profile;
    document.getElementById('modal-title').innerText = "Cài đặt: " + profile;
    
    // Default to first tab
    switchSettingsTab('tab-general');
    
    try {
        const response = await fetch(`/api/profile_config/${encodeURIComponent(profile)}`);
        const config = await response.json();
        
        const aiSource = config.ai_source || 'google';
        const aiSourceRadio = document.querySelector(`input[name="set_ai_source"][value="${aiSource}"]`);
        if (aiSourceRadio) aiSourceRadio.checked = true;

        const gptLimitAction = config.gpt_limit_action || 'wait_limit';
        const gptLimitRadio = document.querySelector(`input[name="set_gpt_limit_action"][value="${gptLimitAction}"]`);
        if (gptLimitRadio) gptLimitRadio.checked = true;
        
        const isActive = config.is_active !== false;
        document.getElementById('set_is_active').checked = isActive;
        
        document.getElementById('set_status_base').value = config.status_base || '';
        document.getElementById('set_prompt_base').value = config.prompt_base || '';
        document.getElementById('set_output_txt_dir').value = config.output_txt_dir || '';
        document.getElementById('set_input_img_dir').value = config.input_img_dir || '';
        document.getElementById('set_prompt_img').value = config.prompt_img || '';
        document.getElementById('set_output_img_dir').value = config.output_img_dir || '';
        document.getElementById('set_fanpage_name').value = config.fanpage_name || '';
        
        // Populate new scraper settings
        document.getElementById('set_instagram_urls').value = (config.instagram_urls || []).join('\n');
        document.getElementById('set_x_urls').value = (config.x_urls || []).join('\n');
        document.getElementById('set_threads_urls').value = (config.threads_urls || []).join('\n');
        document.getElementById('set_scan_times').value = config.scan_times || '';
        document.getElementById('set_scan_limit').value = config.scan_limit || 10;
        if (document.getElementById('set_reup_media_type')) {
            document.getElementById('set_reup_media_type').value = config.reup_media_type || 'all';
        }
        
        // Render danh sách link Fanpage từ config
        const container = document.getElementById('fanpage-urls-container');
        if (container) {
            container.innerHTML = '';
            let urls = [];
            if (config.fanpage_urls && Array.isArray(config.fanpage_urls)) {
                urls = config.fanpage_urls;
            } else if (config.fanpage_url) {
                urls = config.fanpage_url.split(/[\n,]+/).map(u => u.trim()).filter(u => u);
            }
            
            if (urls.length === 0) {
                addFanpageInput('');
            } else {
                urls.forEach(url => addFanpageInput(url));
            }
        }
        
        document.getElementById('settings-modal').style.display = 'block';
    } catch (e) {
        console.error("Lỗi khi fetch config:", e);
    }
}

function closeSettings() {
    document.getElementById('settings-modal').style.display = 'none';
}

async function saveSettings() {
    if (!currentProfileEdit) return;
    
    // Thu thập và kiểm tra trùng lặp các link Fanpage
    const fanpageUrlInputs = document.querySelectorAll('.fanpage-url-input');
    const fanpageUrls = [];
    const seenAssetIds = {};
    const duplicates = [];
    let hasDuplicate = false;
    
    fanpageUrlInputs.forEach((input, index) => {
        const url = input.value.trim();
        if (!url) return;
        fanpageUrls.push(url);
        
        const assetId = getFacebookAssetId(url);
        if (assetId) {
            if (seenAssetIds[assetId]) {
                duplicates.push(`Ô nhập số ${index + 1} trùng với ô số ${seenAssetIds[assetId]} (Định danh/Asset ID: ${assetId})`);
                hasDuplicate = true;
            } else {
                seenAssetIds[assetId] = index + 1;
            }
        }
    });
    
    if (hasDuplicate) {
        alert("⚠️ Phát hiện các Fanpage trùng lặp:\n" + duplicates.join("\n") + "\nVui lòng xóa hoặc chỉnh sửa các link bị trùng trước khi lưu.");
        return;
    }
    
    const config = {
        is_active: document.getElementById('set_is_active').checked,
        ai_source: document.querySelector('input[name="set_ai_source"]:checked').value,
        gpt_limit_action: document.querySelector('input[name="set_gpt_limit_action"]:checked').value,
        status_base: document.getElementById('set_status_base').value,
        prompt_base: document.getElementById('set_prompt_base').value,
        output_txt_dir: document.getElementById('set_output_txt_dir').value,
        input_img_dir: document.getElementById('set_input_img_dir').value,
        prompt_img: document.getElementById('set_prompt_img').value,
        output_img_dir: document.getElementById('set_output_img_dir').value,
        fanpage_name: document.getElementById('set_fanpage_name').value,
        fanpage_urls: fanpageUrls,
        fanpage_url: fanpageUrls.join('\n'),
        instagram_urls: document.getElementById('set_instagram_urls').value.split('\n').map(s => s.trim()).filter(s => s),
        x_urls: document.getElementById('set_x_urls').value.split('\n').map(s => s.trim()).filter(s => s),
        threads_urls: document.getElementById('set_threads_urls').value.split('\n').map(s => s.trim()).filter(s => s),
        scan_times: document.getElementById('set_scan_times').value.trim(),
        scan_limit: parseInt(document.getElementById('set_scan_limit').value) || 10,
        reup_media_type: document.getElementById('set_reup_media_type') ? document.getElementById('set_reup_media_type').value : 'all'
    };
    
    try {
        const response = await fetch(`/api/profile_config/${encodeURIComponent(currentProfileEdit)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await response.json();
        if (data.success) {
            alert("Đã lưu thành công cho " + currentProfileEdit);
            closeSettings();
        } else {
            alert("Lỗi khi lưu!");
        }
    } catch (e) {
        alert("Lỗi khi lưu!");
    }
}

// Status Updates
function updateLog(profile, message) {
    const logList = document.getElementById(`log-list-${profile}`);
    if (logList) {
        const li = document.createElement('li');
        li.textContent = message;
        logList.appendChild(li);
        const consoleDiv = document.getElementById(`console-${profile}`);
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }
}

function applyStatusStyle(profile, status) {
    const badge = document.getElementById(`status-badge-${profile}`);
    if (!badge) return;
    
    // Cập nhật chấm tròn trạng thái (indicator dot)
    const indicator = document.getElementById(`indicator-${profile}`);
    if (indicator) {
        indicator.className = 'status-indicator-dot';
        const s = status.toLowerCase();
        if (s.includes('running') || status === "Running") {
            indicator.classList.add('active-running');
        } else if (s.includes('generating') || s.includes('ai')) {
            indicator.classList.add('active-generating');
        } else if (s.includes('posting') || s.includes('fanpage')) {
            indicator.classList.add('active-posting');
        } else {
            indicator.classList.add('active-idle');
        }
    }
    
    // Nếu status có chứa thời gian đếm ngược (VD: Wait: 00:05:30 hoặc Lỗi... (Wait: 00:05:30))
    const countdownSpan = document.getElementById(`countdown-${profile}`);
    if (status.includes("Wait:")) {
        const idx = status.indexOf("Wait:");
        const waitStr = status.substring(idx);
        const parts = waitStr.split(":");
        if (parts.length >= 4) {
            const timeStr = parts.slice(1).join(":").replace(")", "").trim();
            if(countdownSpan) {
                countdownSpan.textContent = timeStr;
                countdownSpan.style.display = 'inline-block';
            }
            
            let badgeText = status.substring(0, idx).trim().replace("(", "").trim();
            if (!badgeText) {
                badge.textContent = "Đang chờ";
                badge.className = 'status-badge status-idle';
            } else {
                badge.textContent = badgeText;
                if (badgeText.includes("Hết hạn GPT") || badgeText.includes("Chờ thử lại")) {
                    badge.className = 'status-badge status-posting';
                } else {
                    badge.className = 'status-badge status-stopping';
                }
            }
            return;
        }
    } else {
        if(countdownSpan) {
            countdownSpan.textContent = "";
            countdownSpan.style.display = 'none';
        }
    }
    
    // Nếu không phải Wait
    if(status === "Running") {
        badge.textContent = "Đang chạy";
        badge.className = 'status-badge status-generating';
    } else if(status === "Idle" || status === "Waiting") {
        badge.textContent = "Đang chờ";
        badge.className = 'status-badge status-idle';
    } else {
        badge.textContent = status;
        badge.className = 'status-badge'; 
        const s = status.toLowerCase();
        if (s.includes('idle') || s.includes('waiting')) badge.classList.add('status-idle');
        else if (s.includes('generating') || s.includes('ai') || s.includes('running')) badge.classList.add('status-generating');
        else if (s.includes('posting') || s.includes('fanpage') || s.includes('hết hạn gpt') || s.includes('chờ thử lại') || s.includes('thử lại')) badge.classList.add('status-posting');
        else if (s.includes('stopping') || s.includes('missing')) badge.classList.add('status-stopping');
        else badge.classList.add('status-running');
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        for (const [profile, info] of Object.entries(data)) {
            applyStatusStyle(profile, info.status);
            
            // Cập nhật dữ liệu Mini Dashboard
            if (info.mini_stats) {
                const stats = info.mini_stats;
                
                // 1. Tổng bài viết đã reup
                const totalEl = document.getElementById(`mini-val-total-${profile}`);
                if (totalEl) totalEl.textContent = stats.total_posts || 0;
                
                // 2. Định dạng Ảnh/Video
                const mediaEl = document.getElementById(`mini-val-media-${profile}`);
                if (mediaEl) mediaEl.textContent = `${stats.image_count || 0}/${stats.video_count || 0}`;
                
                // 3. Số bài trùng lặp (skipped)
                const skippedEl = document.getElementById(`mini-val-skipped-${profile}`);
                if (skippedEl) skippedEl.textContent = stats.skipped_count || 0;
                
                // 4. Số lỗi
                const errorsEl = document.getElementById(`mini-val-errors-${profile}`);
                const errorItem = document.getElementById(`mini-item-errors-${profile}`);
                if (errorsEl) {
                    errorsEl.textContent = stats.total_errors || 0;
                    if (stats.total_errors > 0) {
                        errorsEl.style.color = '#f87171'; // Đỏ sáng
                        if (errorItem) {
                            errorItem.style.background = 'rgba(244, 63, 94, 0.1)';
                            errorItem.style.borderColor = 'rgba(244, 63, 94, 0.2)';
                        }
                    } else {
                        errorsEl.style.color = '#fff';
                        if (errorItem) {
                            errorItem.style.background = 'rgba(255, 255, 255, 0.015)';
                            errorItem.style.borderColor = 'rgba(255, 255, 255, 0.02)';
                        }
                    }
                }
                
                // 5. Nguồn cào (Hiển thị icon/nhãn)
                const sourcesEl = document.getElementById(`mini-val-sources-${profile}`);
                if (sourcesEl) {
                    let sourcesHtml = [];
                    if (stats.has_instagram) sourcesHtml.push(`<span style="color: #f43f5e; font-weight: 600;">📸 Insta</span>`);
                    if (stats.has_x) sourcesHtml.push(`<span style="color: #38bdf8; font-weight: 600;">🐦 X</span>`);
                    if (stats.has_threads) sourcesHtml.push(`<span style="color: #fff; font-weight: 600;">🧵 Threads</span>`);
                    
                    if (sourcesHtml.length > 0) {
                        sourcesEl.innerHTML = sourcesHtml.join(' • ');
                    } else {
                        sourcesEl.innerHTML = `<span style="color: var(--text-muted); font-style: italic;">Chưa cấu hình</span>`;
                    }
                }
                
                // 6. Tên Fanpage đích
                const fanpageEl = document.getElementById(`mini-val-fanpage-${profile}`);
                if (fanpageEl) {
                    fanpageEl.textContent = stats.fanpage_name || "-";
                    fanpageEl.title = stats.fanpage_name || "";
                }
            }
            
            const logList = document.getElementById(`log-list-${profile}`);
            if (logList && info.logs.length > 0) {
                const currentLastLog = logList.lastElementChild ? logList.lastElementChild.textContent : "";
                const newLastLog = info.logs[info.logs.length - 1];
                if (currentLastLog !== newLastLog) {
                    logList.innerHTML = ''; 
                    info.logs.forEach(msg => {
                        const li = document.createElement('li');
                        li.textContent = msg;
                        logList.appendChild(li);
                    });
                    const consoleDiv = document.getElementById(`console-${profile}`);
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                }
            }
        }
    } catch (e) { console.error("Lỗi khi fetch status:", e); }
}

async function openFacebookModal(profile) {
    currentProfileEdit = profile;
    document.getElementById('facebook-modal-title').innerText = "Cài đặt Facebook: " + profile;
    
    try {
        const response = await fetch(`/api/profile_config/${encodeURIComponent(profile)}`);
        const config = await response.json();
        
        document.getElementById('set_facebook_account').value = config.facebook_account || '';
        document.getElementById('facebook-modal').style.display = 'block';
    } catch (e) {
        console.error("Lỗi khi fetch config:", e);
        alert("Lỗi khi tải cấu hình!");
    }
}

function closeFacebookModal() {
    document.getElementById('facebook-modal').style.display = 'none';
}

async function saveFacebookAccount() {
    if (!currentProfileEdit) return;
    
    const fbAccount = document.getElementById('set_facebook_account').value.trim();
    
    try {
        // Lấy cấu hình hiện tại để tránh bị ghi đè mất các trường khác
        const getResponse = await fetch(`/api/profile_config/${encodeURIComponent(currentProfileEdit)}`);
        const config = await getResponse.json() || {};
        
        config.facebook_account = fbAccount;
        
        const response = await fetch(`/api/profile_config/${encodeURIComponent(currentProfileEdit)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await response.json();
        if (data.success) {
            alert("Đã lưu tài khoản Facebook thành công cho " + currentProfileEdit);
            closeFacebookModal();
        } else {
            alert("Lỗi khi lưu tài khoản Facebook!");
        }
    } catch (e) {
        console.error("Lỗi khi lưu tài khoản Facebook:", e);
        alert("Lỗi khi lưu tài khoản Facebook!");
    }
}

function toggleConsole(profile) {
    const card = document.getElementById(`card-${profile}`);
    if (!card) return;
    const consoleWindow = card.querySelector('.console-window');
    if (!consoleWindow) return;
    
    if (consoleWindow.style.display === 'none' || !consoleWindow.style.display) {
        consoleWindow.style.display = 'block';
        const consoleDiv = document.getElementById(`console-${profile}`);
        if (consoleDiv) consoleDiv.scrollTop = consoleDiv.scrollHeight;
    } else {
        consoleWindow.style.display = 'none';
    }
}

function toggleLogDropdown(profile) {
    if (window.event) {
        window.event.stopPropagation();
    }
    // Close other dropdowns
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (menu.id !== `log-dropdown-${profile}`) {
            menu.classList.remove('show');
        }
    });
    
    const menu = document.getElementById(`log-dropdown-${profile}`);
    if (menu) {
        menu.classList.toggle('show');
    }
}

function copyProfileLog(profile) {
    const logList = document.getElementById(`log-list-${profile}`);
    if (!logList) return;
    const logsText = Array.from(logList.children).map(li => li.textContent).join('\n');
    
    navigator.clipboard.writeText(logsText).then(() => {
        alert(`Đã copy toàn bộ logs của profile "${profile}" vào Clipboard!`);
    }).catch(err => {
        console.error("Lỗi khi copy log:", err);
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = logsText;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            alert(`Đã copy toàn bộ logs của profile "${profile}" vào Clipboard!`);
        } catch (e) {
            alert("Không thể tự động copy log. Hãy quét chọn thủ công.");
        }
        document.body.removeChild(textarea);
    });
}

// Global Controls Accordion Logic
function toggleGlobalControls() {
    const container = document.querySelector('.global-controls');
    const arrow = document.getElementById('global-controls-arrow');
    const body = document.getElementById('global-controls-body');
    if (!container || !arrow || !body) return;
    
    const isCollapsed = container.classList.toggle('collapsed');
    
    if (isCollapsed) {
        arrow.style.transform = 'rotate(-90deg)';
        localStorage.setItem('global_controls_collapsed', 'true');
    } else {
        arrow.style.transform = 'rotate(0deg)';
        localStorage.setItem('global_controls_collapsed', 'false');
        body.style.maxHeight = '1000px';
    }
}

function initGlobalControlsAccordion() {
    const collapsed = localStorage.getItem('global_controls_collapsed');
    const container = document.querySelector('.global-controls');
    const arrow = document.getElementById('global-controls-arrow');
    const body = document.getElementById('global-controls-body');
    if (!container || !arrow || !body) return;
    
    if (collapsed === 'true') {
        container.classList.add('collapsed');
        arrow.style.transform = 'rotate(-90deg)';
    } else {
        body.style.maxHeight = '1000px';
    }
}

// Card Profile Toolbar Dropdown Logic
function toggleDropdown(profile) {
    // Ngăn chặn sự kiện click lan ra ngoài
    if (window.event) {
        window.event.stopPropagation();
    }
    
    // Đóng toàn bộ các dropdown khác
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (menu.id !== `dropdown-${profile}`) {
            menu.classList.remove('show');
        }
    });
    
    const menu = document.getElementById(`dropdown-${profile}`);
    if (menu) {
        menu.classList.toggle('show');
    }
}

// Tự động đóng dropdown khi click bất cứ đâu ngoài menu
document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
    });
});

let currentDashboardProfile = "";
let dashboardIntervalId = null;

function openDashboard(profile) {
    currentDashboardProfile = profile;
    document.getElementById('dashboard-modal').style.display = 'block';
    
    // Reset views
    document.getElementById('dashboard-profile-name-sub').textContent = "Đang tải dữ liệu...";
    document.getElementById('dash-stat-live').textContent = "Đang kết nối...";
    
    // Tải dữ liệu ngay lập tức
    updateDashboardData(profile);
    
    // Tự động làm mới mỗi 3 giây để cập nhật số liệu thời gian thực
    if (dashboardIntervalId) clearInterval(dashboardIntervalId);
    dashboardIntervalId = setInterval(() => {
        const modal = document.getElementById('dashboard-modal');
        if (modal && modal.style.display === 'block') {
            updateDashboardData(currentDashboardProfile);
        } else {
            clearInterval(dashboardIntervalId);
        }
    }, 3000);
}

function closeDashboard() {
    document.getElementById('dashboard-modal').style.display = 'none';
    if (dashboardIntervalId) {
        clearInterval(dashboardIntervalId);
        dashboardIntervalId = null;
    }
}

function refreshDashboard() {
    if (currentDashboardProfile) {
        updateDashboardData(currentDashboardProfile);
    }
}

async function updateDashboardData(profile) {
    try {
        // Tải config & stats từ API song song
        const [configRes, statsRes] = await Promise.all([
            fetch(`/api/profile_config/${encodeURIComponent(profile)}`),
            fetch(`/api/dashboard/${encodeURIComponent(profile)}`)
        ]);
        
        const config = await configRes.json();
        const stats = await statsRes.json();
        
        if (!config || !stats) return;
        
        // 1. Tiêu đề và Subtitle
        document.getElementById('dashboard-title').textContent = "📊 Dashboard: " + profile;
        document.getElementById('dashboard-profile-name-sub').textContent = config.fanpage_name ? `Fanpage: ${config.fanpage_name}` : "Chưa đặt tên gợi nhớ Fanpage";
        
        // 2. Chấm trạng thái và Badge
        const dot = document.getElementById('dashboard-status-dot');
        const text = document.getElementById('dashboard-status-text');
        
        const status = stats.status || "Idle";
        text.textContent = status;
        
        if (dot) {
            dot.className = 'status-indicator-dot';
            const s = status.toLowerCase();
            if (s.includes('running') || status === "Running") {
                dot.classList.add('active-running');
                document.getElementById('dash-stat-live').textContent = "Đang chạy";
                document.getElementById('dash-stat-live-detail').textContent = "Tiến trình cào/đăng bài đang active";
            } else if (s.includes('generating') || s.includes('ai')) {
                dot.classList.add('active-generating');
                document.getElementById('dash-stat-live').textContent = "Xử lý AI";
                document.getElementById('dash-stat-live-detail').textContent = "Đang viết status / vẽ ảnh qua AI";
            } else if (s.includes('posting') || s.includes('fanpage')) {
                dot.classList.add('active-posting');
                document.getElementById('dash-stat-live').textContent = "Đăng bài";
                document.getElementById('dash-stat-live-detail').textContent = "Đang đẩy file và điền composer FB";
            } else if (s.includes('missing') || s.includes('deactivated')) {
                dot.classList.add('active-idle');
                document.getElementById('dash-stat-live').textContent = "Tạm dừng";
                document.getElementById('dash-stat-live-detail').textContent = "Profile chưa kích hoạt hoặc thiếu cấu hình";
            } else {
                dot.classList.add('active-idle');
                document.getElementById('dash-stat-live').textContent = "Đang chờ";
                document.getElementById('dash-stat-live-detail').textContent = "Đang nghỉ giữa các vòng chạy";
            }
        }
        
        // 3. Số liệu thống kê
        document.getElementById('dash-stat-total').textContent = stats.total_posts || 0;
        document.getElementById('dash-stat-images').textContent = stats.image_count || 0;
        document.getElementById('dash-stat-videos').textContent = stats.video_count || 0;
        document.getElementById('dash-stat-skipped').textContent = stats.skipped_count || 0;
        document.getElementById('dash-stat-errors').textContent = stats.total_errors || 0;
        
        const errCard = document.getElementById('dash-stat-error-card');
        const errDetail = document.getElementById('dash-stat-errors-detail');
        if (stats.total_errors > 0) {
            errCard.style.background = 'rgba(244, 63, 94, 0.15)';
            errCard.style.borderColor = 'rgba(244, 63, 94, 0.4)';
            errDetail.textContent = "Phát hiện sự cố! Xem chi tiết ở dưới";
            errDetail.style.color = '#f87171';
        } else {
            errCard.style.background = 'rgba(244, 63, 94, 0.06)';
            errCard.style.borderColor = 'rgba(244, 63, 94, 0.15)';
            errDetail.textContent = "Hoạt động an toàn";
            errDetail.style.color = 'rgba(255,255,255,0.5)';
        }
        
        // 4. Hiển thị liên kết nguồn & đích
        const renderList = (arr) => {
            if (!arr || arr.length === 0) return `<span style="color: var(--text-muted)">[Chưa cấu hình]</span>`;
            return arr.map(link => `<a href="${link}" target="_blank" style="color: #60a5fa; text-decoration: none; display: block; margin-bottom: 2px; transition: color 0.2s;" onmouseover="this.style.color='#93c5fd'" onmouseout="this.style.color='#60a5fa'">🔗 ${link}</a>`).join('');
        };
        
        document.getElementById('dash-src-instagram').innerHTML = renderList(stats.sources.instagram);
        document.getElementById('dash-src-x').innerHTML = renderList(stats.sources.x);
        document.getElementById('dash-src-threads').innerHTML = renderList(stats.sources.threads);
        document.getElementById('dash-dest-fanpage').innerHTML = renderList(stats.sources.fanpages);
        
        // 5. Hiển thị đường dẫn lưu trữ
        document.getElementById('dash-path-input').textContent = config.input_img_dir || "-";
        document.getElementById('dash-path-text').textContent = config.output_txt_dir || "-";
        document.getElementById('dash-path-image').textContent = config.output_img_dir || "-";
        
        // 6. Mục lỗi gần nhất
        const errSection = document.getElementById('dash-error-section');
        const errList = document.getElementById('dash-error-list');
        if (stats.errors && stats.errors.length > 0) {
            errSection.style.display = 'block';
            errList.innerHTML = stats.errors.map(err => `
                <li style="margin-bottom: 4px; padding: 6px 10px; background: rgba(0,0,0,0.25); border-left: 3px solid #f43f5e; border-radius: 4px; word-break: break-all;">
                    ${err}
                </li>
            `).join('');
        } else {
            errSection.style.display = 'none';
        }
        
        // 7. Lịch sử reup gần nhất (Bảng)
        const tableBody = document.getElementById('dash-history-table-body');
        if (stats.history && stats.history.length > 0) {
            tableBody.innerHTML = stats.history.map(row => {
                let badgePlatform = "";
                if (row.platform === "instagram") {
                    badgePlatform = `<span style="background: rgba(244, 63, 94, 0.15); color: #f43f5e; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">Instagram</span>`;
                } else if (row.platform === "x") {
                    badgePlatform = `<span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">X / Twitter</span>`;
                } else if (row.platform === "threads") {
                    badgePlatform = `<span style="background: rgba(255, 255, 255, 0.1); color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">Threads</span>`;
                } else {
                    badgePlatform = `<span style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">${row.platform}</span>`;
                }
                
                let badgeMedia = "";
                if (row.media_type === "image") {
                    badgeMedia = `🖼️ Ảnh`;
                } else if (row.media_type === "video") {
                    badgeMedia = `🎥 Video`;
                } else if (row.media_type === "text") {
                    badgeMedia = `📝 Chữ`;
                } else {
                    badgeMedia = `❓ Lịch sử`;
                }
                
                // Tạo link bài viết gốc và nút Đăng thẳng thủ công
                let actionBtn = "";
                if (row.post_id && row.post_id.length > 2) {
                    let targetUrl = "";
                    if (row.platform === "instagram") targetUrl = `https://www.instagram.com/p/${row.post_id}/`;
                    else if (row.platform === "x") targetUrl = `https://x.com/x/status/${row.post_id}`;
                    else if (row.platform === "threads") targetUrl = `https://www.threads.net/post/${row.post_id}`;
                    
                    if (targetUrl) {
                        actionBtn += `<a href="${targetUrl}" target="_blank" style="display: inline-block; background: rgba(255, 255, 255, 0.05); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.1); padding: 2px 6px; border-radius: 4px; text-decoration: none; font-size: 0.7rem; margin-right: 6px; transition: all 0.2s;" onmouseover="this.style.background='rgba(255, 255, 255, 0.1)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.05)'">Xem ↗</a>`;
                    }
                    
                    actionBtn += `<button onclick="reupPostManual('${profile}', '${row.platform}', '${row.post_id}', this, false)" style="display: inline-block; background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; cursor: pointer; margin-right: 6px; transition: all 0.2s;" onmouseover="this.style.background='rgba(99, 102, 241, 0.3)'" onmouseout="this.style.background='rgba(99, 102, 241, 0.15)'">⚡ Đăng thẳng</button>`;
                    
                    actionBtn += `<button onclick="reupPostManual('${profile}', '${row.platform}', '${row.post_id}', this, true)" style="display: inline-block; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='rgba(16, 185, 129, 0.3)'" onmouseout="this.style.background='rgba(16, 185, 129, 0.15)'">⚡ Đăng gốc</button>`;
                } else {
                    actionBtn = "-";
                }
                
                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.01)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 10px 8px;">${badgePlatform}</td>
                        <td style="padding: 10px 8px; font-family: monospace; font-size: 0.8rem; color: rgba(255,255,255,0.6);">${row.post_id}</td>
                        <td style="padding: 10px 8px; color: var(--text-secondary);">${badgeMedia}</td>
                        <td style="padding: 10px 8px; color: var(--text-secondary); font-size: 0.8rem;">${row.processed_at}</td>
                        <td style="padding: 10px 8px; text-align: right;">${actionBtn}</td>
                    </tr>
                `;
            }).join('');
        } else {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 25px; color: var(--text-muted); font-style: italic;">
                        Chưa có lịch sử reup nào được lưu trữ cho profile này.
                    </td>
                </tr>
            `;
        }
        
        // 8. Cập nhật thời gian
        const now = new Date();
        const pad = (n) => n.toString().padStart(2, '0');
        document.getElementById('dash-last-updated').textContent = `Cập nhật lần cuối: ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        
    } catch (e) {
        console.error("Lỗi khi update dashboard stats:", e);
    }
}

setInterval(fetchStatus, 2000);
fetchStatus();
loadGlobalConfig();

document.addEventListener('DOMContentLoaded', () => {
    initGlobalControlsAccordion();
});

let pendingReupRequest = null;

function closeReupModeModal() {
    document.getElementById('reup-mode-modal').style.display = 'none';
}

function confirmReupMode(testMode) {
    if (!pendingReupRequest) return;
    const { profile, platform, postId, buttonEl, bypassAi } = pendingReupRequest;
    closeReupModeModal();
    executeReupPostManual(profile, platform, postId, buttonEl, bypassAi, testMode);
}

function reupPostManual(profile, platform, postId, buttonEl, bypassAi = false) {
    const modeName = bypassAi ? "Gốc (Không qua AI)" : "Thẳng (Có qua AI)";
    document.getElementById('reup-mode-desc').innerHTML = `Bạn muốn chạy đăng thủ công bài viết này (<strong>${platform.toUpperCase()} ID: ${postId}</strong>) dưới chế độ Đăng <strong>${modeName}</strong> nào?`;
    
    pendingReupRequest = { profile, platform, postId, buttonEl, bypassAi };
    document.getElementById('reup-mode-modal').style.display = 'flex';
}

async function executeReupPostManual(profile, platform, postId, buttonEl, bypassAi, testMode) {
    // Disable button and show loading state
    const originalHtml = buttonEl.innerHTML;
    buttonEl.disabled = true;
    buttonEl.innerHTML = "⏳ Đang đăng...";
    buttonEl.style.background = "rgba(245, 158, 11, 0.2)";
    buttonEl.style.color = "#fbbf24";
    buttonEl.style.borderColor = "rgba(245, 158, 11, 0.4)";
    
    try {
        const response = await fetch(`/api/reup_post_manual/${encodeURIComponent(profile)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                platform: platform, 
                post_id: postId, 
                bypass_ai: bypassAi,
                test_mode: testMode
            })
        });
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
        } else {
            alert("Lỗi: " + data.message);
            // Restore button if failed to trigger
            buttonEl.disabled = false;
            buttonEl.innerHTML = originalHtml;
            if (bypassAi) {
                buttonEl.style.background = "rgba(16, 185, 129, 0.15)";
                buttonEl.style.color = "#34d399";
                buttonEl.style.borderColor = "rgba(16, 185, 129, 0.3)";
            } else {
                buttonEl.style.background = "rgba(99, 102, 241, 0.15)";
                buttonEl.style.color = "#a5b4fc";
                buttonEl.style.borderColor = "rgba(99, 102, 241, 0.3)";
            }
        }
    } catch (e) {
        console.error(e);
        alert("Lỗi kết nối khi gửi lệnh đăng thủ công!");
        buttonEl.disabled = false;
        buttonEl.innerHTML = originalHtml;
        if (bypassAi) {
            buttonEl.style.background = "rgba(16, 185, 129, 0.15)";
            buttonEl.style.color = "#34d399";
            buttonEl.style.borderColor = "rgba(16, 185, 129, 0.3)";
        } else {
            buttonEl.style.background = "rgba(99, 102, 241, 0.15)";
            buttonEl.style.color = "#a5b4fc";
            buttonEl.style.borderColor = "rgba(99, 102, 241, 0.3)";
        }
    }
}
