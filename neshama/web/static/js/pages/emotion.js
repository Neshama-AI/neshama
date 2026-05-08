/**
 * Emotion Page - Emotion timeline and history
 */

let emotionHistory = [];
let emotionChart = null;

// Render Emotion Page
async function renderEmotion() {
    const container = document.getElementById('page-emotion');
    
    try {
        const [currentRes, historyRes] = await Promise.all([
            API.emotion.getCurrent(),
            API.emotion.getHistory(24)
        ]);
        
        emotionHistory = historyRes.data.history || [];
        
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">${t('emotion.title')}</h1>
                <p class="page-subtitle">${t('emotion.subtitle')}</p>
            </div>
            
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('emotion.currentState')}</span>
                        <span class="tag tag-amber">${t('dashboard.live')}</span>
                    </div>
                    <div id="current-emotion-display" class="mt-4">
                        ${renderCurrentEmotion(currentRes.data)}
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${t('emotion.statistics')}</span>
                    </div>
                    <div id="emotion-stats" class="mt-4">
                        ${renderEmotionStats(historyRes.data.stats)}
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('emotion.intensityTimeline')}</span>
                    <div class="flex gap-2">
                        <select id="emotion-time-range" class="form-input" style="width: auto;" onchange="changeEmotionTimeRange()">
                            <option value="6">${t('emotion.last6h')}</option>
                            <option value="12">${t('emotion.last12h')}</option>
                            <option value="24" selected>${t('emotion.last24h')}</option>
                            <option value="48">${t('emotion.last48h')}</option>
                            <option value="168">${t('emotion.lastWeek')}</option>
                        </select>
                    </div>
                </div>
                <div class="canvas-container" style="height: 250px;">
                    <canvas id="emotion-timeline-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('emotion.distribution')}</span>
                </div>
                <div class="canvas-container" style="height: 200px;">
                    <canvas id="emotion-distribution-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <span class="card-title">${t('emotion.recentEvents')}</span>
                </div>
                <div id="emotion-events" class="mt-3">
                    ${renderEmotionEvents(historyRes.data.events)}
                </div>
            </div>
        `;
        
        // Draw charts
        setTimeout(() => {
            drawEmotionTimeline(emotionHistory);
            drawEmotionDistribution(emotionHistory);
        }, 100);
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon" style="font-size:24px;color:#ff6b35;">Emotion</div>
                <div class="empty-state-text">${t('emotion.failedLoad')}</div>
                <button class="btn btn-primary mt-4" onclick="renderEmotion()">${t('common.retry')}</button>
            </div>
        `;
    }
}

// Render current emotion
function renderCurrentEmotion(emotion) {
    return `
        <div class="flex items-center gap-4">
            <div style="font-size: 80px;">${emotion.primary.emoji}</div>
            <div>
                <div style="font-size: 28px; font-weight: 600; color: ${emotion.primary.color};">
                    ${emotion.primary.category.charAt(0).toUpperCase() + emotion.primary.category.slice(1)}
                </div>
                <div class="mt-2">
                    <div class="form-label">${t('emotion.intensity')}</div>
                    <div class="progress-bar" style="width: 200px;">
                        <div class="progress-fill" style="width: ${emotion.primary.intensity * 100}%; background: ${emotion.primary.color};"></div>
                    </div>
                    <span class="text-accent">${(emotion.primary.intensity * 100).toFixed(0)}%</span>
                </div>
                ${emotion.secondary ? `
                    <div class="mt-3" style="padding-top: 12px; border-top: 1px solid var(--border-color);">
                        <span class="text-muted">${t('emotion.secondary')}: </span>
                        <span>${emotion.secondary.emoji} ${emotion.secondary.category}</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Render emotion stats
function renderEmotionStats(stats) {
    if (!stats) return `<div class="text-muted">${t('emotion.noStats')}</div>`;
    
    return `
        <div class="grid-2 gap-4">
            <div>
                <div class="stat-value">${(stats.avg_intensity * 100).toFixed(0)}%</div>
                <div class="stat-label">${t('emotion.avgIntensity')}</div>
            </div>
            <div>
                <div class="stat-value" style="text-transform: capitalize;">${stats.dominant_emotion}</div>
                <div class="stat-label">${t('emotion.dominantEmotion')}</div>
            </div>
            <div>
                <div class="stat-value">${stats.emotion_variance.toFixed(2)}</div>
                <div class="stat-label">${t('emotion.variance')}</div>
            </div>
            <div>
                <div class="stat-value">${stats.peak_times?.length || 0}</div>
                <div class="stat-label">${t('emotion.peakTimes')}</div>
            </div>
        </div>
    `;
}

// Render emotion events
function renderEmotionEvents(events) {
    if (!events || events.length === 0) {
        return `<div class="text-muted">${t('emotion.noEvents')}</div>`;
    }
    
    return events.map(event => `
        <div class="flex items-center justify-between mb-2" style="padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
            <div class="flex items-center gap-3">
                <span style="font-size: 24px;">${getEmotionEmoji(event.emotion)}</span>
                <div>
                    <div style="font-weight: 500;">${event.event}</div>
                    <div class="text-muted" style="font-size: 12px;">${event.time}</div>
                </div>
            </div>
            <div class="text-accent">${(event.intensity * 100).toFixed(0)}%</div>
        </div>
    `).join('');
}

// Draw emotion timeline chart
function drawEmotionTimeline(history) {
    const canvas = document.getElementById('emotion-timeline-chart');
    if (!canvas || !history.length) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 250;
    
    // Clear
    ctx.clearRect(0, 0, width, height);
    
    // Margins
    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 4; i++) {
        const y = margin.top + (chartHeight * i / 4);
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(width - margin.right, y);
        ctx.stroke();
        
        // Label
        ctx.fillStyle = '#64748B';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`${(1 - i / 4).toFixed(1)}`, margin.left - 8, y + 3);
    }
    
    // Sample data (every Nth point)
    const step = Math.max(1, Math.floor(history.length / 50));
    const sampledData = history.filter((_, i) => i % step === 0);
    
    // Draw intensity line
    ctx.beginPath();
    ctx.strokeStyle = '#7c5cff';
    ctx.lineWidth = 2;
    
    sampledData.forEach((point, i) => {
        const x = margin.left + (i / (sampledData.length - 1)) * chartWidth;
        const y = margin.top + (1 - point.intensity) * chartHeight;
        
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Fill under line
    ctx.lineTo(margin.left + chartWidth, margin.top + chartHeight);
    ctx.lineTo(margin.left, margin.top + chartHeight);
    ctx.closePath();
    ctx.fillStyle = 'rgba(79, 70, 229, 0.2)';
    ctx.fill();
    
    // Draw points
    sampledData.forEach((point, i) => {
        const x = margin.left + (i / (sampledData.length - 1)) * chartWidth;
        const y = margin.top + (1 - point.intensity) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = point.color || '#00d4aa';
        ctx.fill();
    });
    
    // X-axis labels
    ctx.fillStyle = '#64748B';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    
    const labelCount = 6;
    for (let i = 0; i < labelCount; i++) {
        const idx = Math.floor(i * (sampledData.length - 1) / (labelCount - 1));
        const point = sampledData[idx];
        if (point) {
            const x = margin.left + (idx / (sampledData.length - 1)) * chartWidth;
            const time = new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            ctx.fillText(time, x, height - 10);
        }
    }
}

// Draw emotion distribution chart
function drawEmotionDistribution(history) {
    const canvas = document.getElementById('emotion-distribution-chart');
    if (!canvas || !history.length) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth;
    const height = canvas.height = 200;
    
    // Count emotions
    const counts = {};
    history.forEach(point => {
        const cat = point.category;
        counts[cat] = (counts[cat] || 0) + 1;
    });
    
    const colors = {
        'joy': '#00d4aa', 'sadness': '#7c5cff', 'anger': '#ff6b35', 
        'fear': '#7c5cff', 'surprise': '#ff6b35', 'disgust': '#00d4aa',
        'trust': '#7c5cff', 'anticipation': '#00d4aa'
    };
    
    const emojis = {
        'joy': 'Joy', 'sadness': 'Sad', 'anger': 'Anger', 'fear': 'Fear',
        'surprise': 'Surprise', 'disgust': 'Disgust', 'trust': 'Trust', 'anticipation': 'Anticipation'
    };
    
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const total = entries.reduce((sum, [_, count]) => sum + count, 1);
    
    // Bar chart
    const barHeight = 30;
    const gap = 8;
    const maxWidth = width - 100;
    
    ctx.clearRect(0, 0, width, height);
    
    entries.forEach(([category, count], i) => {
        const y = 20 + i * (barHeight + gap);
        const barWidth = (count / total) * maxWidth;
        
        // Background bar
        ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.fillRect(60, y, maxWidth, barHeight);
        
        // Fill bar
        ctx.fillStyle = colors[category] || '#7c5cff';
        ctx.fillRect(60, y, barWidth, barHeight);
        
        // Label
        ctx.fillStyle = '#F8FAFC';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(emojis[category] || category[0], 50, y + 22);
        
        // Percentage
        ctx.textAlign = 'left';
        ctx.fillText(`${((count / total) * 100).toFixed(1)}%`, 70 + barWidth, y + 22);
    });
}

// Change emotion time range
async function changeEmotionTimeRange() {
    const select = document.getElementById('emotion-time-range');
    const hours = parseInt(select.value);
    
    try {
        const res = await API.emotion.getHistory(hours);
        emotionHistory = res.data.history || [];
        drawEmotionTimeline(emotionHistory);
        drawEmotionDistribution(emotionHistory);
    } catch (error) {
        showToast(t('emotion.loadFailed'), 'error');
    }
}

// Refresh emotion data
async function refreshEmotionData() {
    try {
        const res = await API.emotion.getCurrent();
        const display = document.getElementById('current-emotion-display');
        if (display) {
            display.innerHTML = renderCurrentEmotion(res.data);
        }
    } catch (error) {
        console.error('Failed to refresh emotion:', error);
    }
}
