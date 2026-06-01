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
        delay_times: document.getElementById('delay_times').value.split(',').map(s => s.trim()).filter(s => s)
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
        const response = await fetch(`/api/start/${profile}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) updateLog(profile, "Đang gửi lệnh Start...");
        else updateLog(profile, "Lỗi: " + data.message);
    } catch (e) { console.error(e); }
}

async function stopProfile(profile) {
    try {
        const response = await fetch(`/api/stop/${profile}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) updateLog(profile, "Đang gửi lệnh Stop...");
        else updateLog(profile, "Lỗi: " + data.message);
    } catch (e) { console.error(e); }
}

async function clearProfileLog(profile) {
    if (!confirm(`Bạn có chắc muốn xóa sạch log của ${profile} không?`)) return;
    try {
        const response = await fetch(`/api/clear_log/${profile}`, { method: 'POST' });
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
        const response = await fetch(`/api/rename_profile/${oldName}`, {
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
        const response = await fetch(`/api/delete_profile/${profileName}`, {
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
        const response = await fetch(`/api/manual_browser/${profile}`, { method: 'POST' });
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
async function openSettings(profile) {
    currentProfileEdit = profile;
    document.getElementById('modal-title').innerText = "Cài đặt: " + profile;
    try {
        const response = await fetch(`/api/profile_config/${profile}`);
        const config = await response.json();
        
        const aiSource = config.ai_source || 'google';
        const aiSourceRadio = document.querySelector(`input[name="set_ai_source"][value="${aiSource}"]`);
        if (aiSourceRadio) aiSourceRadio.checked = true;
        
        const isActive = config.is_active !== false;
        document.getElementById('set_is_active').checked = isActive;
        
        document.getElementById('set_status_base').value = config.status_base || '';
        document.getElementById('set_prompt_base').value = config.prompt_base || '';
        document.getElementById('set_output_txt_dir').value = config.output_txt_dir || '';
        document.getElementById('set_input_img_dir').value = config.input_img_dir || '';
        document.getElementById('set_prompt_img').value = config.prompt_img || '';
        document.getElementById('set_output_img_dir').value = config.output_img_dir || '';
        document.getElementById('set_fanpage_name').value = config.fanpage_name || '';
        document.getElementById('set_fanpage_url').value = config.fanpage_url || '';
        
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
    
    const config = {
        is_active: document.getElementById('set_is_active').checked,
        ai_source: document.querySelector('input[name="set_ai_source"]:checked').value,
        status_base: document.getElementById('set_status_base').value,
        prompt_base: document.getElementById('set_prompt_base').value,
        output_txt_dir: document.getElementById('set_output_txt_dir').value,
        input_img_dir: document.getElementById('set_input_img_dir').value,
        prompt_img: document.getElementById('set_prompt_img').value,
        output_img_dir: document.getElementById('set_output_img_dir').value,
        fanpage_name: document.getElementById('set_fanpage_name').value,
        fanpage_url: document.getElementById('set_fanpage_url').value,
    };
    
    try {
        const response = await fetch(`/api/profile_config/${currentProfileEdit}`, {
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
    
    // Nếu status có chứa thời gian đếm ngược (VD: Wait: 00:05:30 hoặc Lỗi... (Wait: 00:05:30))
    const countdownSpan = document.getElementById(`countdown-${profile}`);
    if (status.includes("Wait:")) {
        const idx = status.indexOf("Wait:");
        const waitStr = status.substring(idx);
        const parts = waitStr.split(":");
        if (parts.length >= 4) {
            const timeStr = parts.slice(1).join(":").replace(")", "").trim();
            if(countdownSpan) countdownSpan.textContent = timeStr;
            
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
        if(countdownSpan) countdownSpan.textContent = "";
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
        else if (s.includes('posting') || s.includes('fanpage') || s.includes('hết hạn gpt') || s.includes('chờ thử lại')) badge.classList.add('status-posting');
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

setInterval(fetchStatus, 2000);
fetchStatus();
loadGlobalConfig();
