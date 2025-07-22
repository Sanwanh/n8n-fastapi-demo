// 郵件發送系統 JavaScript
// 市場分析報告郵件發送功能

console.log('📧 郵件發送系統載入中...');

// 全域變數
let currentMarketData = null;
let autoRefreshInterval = null;

// 初始化函數
function initializeMailSystem() {
    console.log('🚀 初始化郵件發送系統...');

    // 載入初始數據
    loadMarketData();

    // 綁定事件
    bindEvents();

    // 設置自動刷新
    startAutoRefresh();

    console.log('✅ 郵件發送系統初始化完成');
}

// 載入市場數據
async function loadMarketData() {
    try {
        updateStatus('loading', '載入中...');

        const response = await fetch('/api/current-data');
        const result = await response.json();

        if (result.data && Object.keys(result.data).length > 0) {
            currentMarketData = result.data;
            displayMarketData(result.data);
            updateStatus('connected', '已更新');
            validateForm();
        } else {
            displayNoData();
            updateStatus('waiting', '等待數據...');
        }
    } catch (error) {
        console.error('載入市場數據失敗:', error);
        displayError('無法載入市場數據: ' + error.message);
        updateStatus('error', '連接錯誤');
    }
}

// 顯示市場數據
function displayMarketData(data) {
    const sentimentClass = getSentimentClass(data.average_sentiment_score);
    const sentimentText = getSentimentText(data.average_sentiment_score);

    document.getElementById('market-data-display').innerHTML = `
        <div class="market-data">
            <div class="data-row">
                <div class="data-label">
                    <i class="fas fa-chart-line"></i>
                    情感分析分數
                </div>
                <div class="data-value">
                    <span class="sentiment-score ${sentimentClass}">
                        ${data.average_sentiment_score?.toFixed(3)} (${sentimentText})
                    </span>
                </div>
            </div>

            <div class="data-row">
                <div class="data-label">
                    <i class="fas fa-calendar-day"></i>
                    市場日期
                </div>
                <div class="data-value">${data.market_date || '今日'}</div>
            </div>

            <div class="data-row">
                <div class="data-label">
                    <i class="fas fa-clock"></i>
                    接收時間
                </div>
                <div class="data-value">${data.received_time}</div>
            </div>

            <div class="data-row">
                <div class="data-label">
                    <i class="fas fa-shield-alt"></i>
                    風險評估
                </div>
                <div class="data-value">${data.risk_assessment || '未知'}</div>
            </div>

            <div class="data-row full-width">
                <div class="data-label">
                    <i class="fas fa-newspaper"></i>
                    市場分析內容
                </div>
                <div class="market-content">
                    ${formatContent(data.message_content)}
                </div>
            </div>
        </div>
    `;
}

// 顯示無數據
function displayNoData() {
    document.getElementById('market-data-display').innerHTML = `
        <div class="no-data">
            <i class="fas fa-chart-bar"></i>
            <h3>等待市場數據</h3>
            <p>請確認系統已接收到市場分析數據</p>
            <button onclick="loadMarketData()" class="retry-btn">
                <i class="fas fa-refresh"></i>
                重新載入
            </button>
        </div>
    `;
}

// 顯示錯誤
function displayError(message) {
    document.getElementById('market-data-display').innerHTML = `
        <div class="error-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>數據載入失敗</h3>
            <p>${message}</p>
            <button onclick="loadMarketData()" class="retry-btn">
                <i class="fas fa-refresh"></i>
                重試
            </button>
        </div>
    `;
}

// 更新狀態
function updateStatus(status, text) {
    const dot = document.querySelector('#status-indicator .indicator-dot');
    const textElement = document.querySelector('#status-indicator .indicator-text');

    dot.classList.remove('connected', 'error', 'loading');
    if (status !== 'waiting') {
        dot.classList.add(status);
    }
    textElement.textContent = text;
}

// 表單驗證
function validateForm() {
    const recipient = document.getElementById('recipient').value;
    const subject = document.getElementById('subject').value;
    const hasData = currentMarketData !== null;

    const isValid = recipient && subject && hasData;
    document.getElementById('send-btn').disabled = !isValid;

    // 更新按鈕樣式
    const sendBtn = document.getElementById('send-btn');
    if (isValid) {
        sendBtn.classList.add('ready');
    } else {
        sendBtn.classList.remove('ready');
    }
}

// 綁定事件
function bindEvents() {
    // 表單提交事件
    document.getElementById('mail-form').addEventListener('submit', handleSubmit);

    // 模態框關閉事件
    document.getElementById('result-close').addEventListener('click', hideModal);
    document.getElementById('result-ok').addEventListener('click', hideModal);

    // 表單驗證事件
    const inputs = document.querySelectorAll('#mail-form input[required], #mail-form textarea');
    inputs.forEach(input => {
        input.addEventListener('input', validateForm);
    });

    // 選項變更事件
    const checkboxes = document.querySelectorAll('#mail-form input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', validateForm);
    });
}

// 處理表單提交
async function handleSubmit(e) {
    e.preventDefault();

    if (!currentMarketData) {
        showModal('error', '發送失敗', '沒有可用的市場數據，請等待數據載入完成');
        return;
    }

    setLoadingState(true);

    try {
        const formData = new FormData(e.target);

        const mailData = {
            recipient_email: formData.get('recipient'),
            sender_name: formData.get('sender_name') || '市場分析系統',
            subject: formData.get('subject'),
            custom_message: formData.get('custom_message') || '',
            include_charts: formData.has('include_charts'),
            include_recommendations: formData.has('include_recommendations'),
            include_risk_warning: formData.has('include_risk_warning')
        };

        console.log('📧 發送郵件數據:', mailData);

        const response = await fetch('/api/send-mail-to-n8n', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mailData)
        });

        const result = await response.json();

        if (response.ok) {
            showModal('success', '發送成功', `郵件已成功發送給 ${mailData.recipient_email}`);
            // 清空表單
            e.target.reset();
            validateForm();
        } else {
            showModal('error', '發送失敗', result.detail || '發送失敗，請檢查網路連接');
        }

    } catch (error) {
        console.error('發送郵件失敗:', error);
        showModal('error', '網路錯誤', '請檢查網路連接後重試');
    } finally {
        setLoadingState(false);
    }
}

// 設置加載狀態
function setLoadingState(loading) {
    const sendBtn = document.getElementById('send-btn');
    if (loading) {
        sendBtn.classList.add('loading');
        sendBtn.disabled = true;
    } else {
        sendBtn.classList.remove('loading');
        validateForm();
    }
}

// 顯示模態框
function showModal(type, title, message) {
    const modal = document.getElementById('result-modal');
    const icon = document.getElementById('result-icon');
    const titleEl = document.getElementById('result-title');
    const messageEl = document.getElementById('result-message');

    icon.className = `modal-icon ${type}`;
    icon.innerHTML = type === 'success' ?
        '<i class="fas fa-check-circle"></i>' :
        '<i class="fas fa-exclamation-circle"></i>';

    titleEl.textContent = title;
    messageEl.textContent = message;
    modal.classList.add('show');

    // 自動關閉成功訊息
    if (type === 'success') {
        setTimeout(() => {
            hideModal();
        }, 3000);
    }
}

// 隱藏模態框
function hideModal() {
    document.getElementById('result-modal').classList.remove('show');
}

// 開始自動刷新
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }

    autoRefreshInterval = setInterval(() => {
        loadMarketData();
    }, 30000); // 每30秒刷新一次
}

// 停止自動刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 輔助函數
function getSentimentClass(score) {
    if (score > 0.1) return 'sentiment-positive';
    if (score < -0.1) return 'sentiment-negative';
    return 'sentiment-neutral';
}

function getSentimentText(score) {
    if (score > 0.6) return '極度樂觀';
    if (score > 0.3) return '樂觀';
    if (score > 0.1) return '略為樂觀';
    if (score > -0.1) return '中性';
    if (score > -0.3) return '略為悲觀';
    if (score > -0.6) return '悲觀';
    return '極度悲觀';
}

function formatContent(content) {
    if (!content) return '無市場分析內容';

    if (content.length > 300) {
        const preview = content.substring(0, 300);
        const remaining = content.substring(300);

        return `
            <span class="content-preview">${preview}</span>
            <span class="content-full" style="display: none;">${remaining}</span>
            <button class="expand-btn" onclick="toggleContent(this)">
                ...展開完整內容
            </button>
        `;
    }

    return content;
}

// 切換內容顯示
function toggleContent(button) {
    const preview = button.previousElementSibling.previousElementSibling;
    const full = button.previousElementSibling;

    if (full.style.display === 'none') {
        preview.style.display = 'none';
        full.style.display = 'inline';
        button.textContent = '收起內容';
    } else {
        preview.style.display = 'inline';
        full.style.display = 'none';
        button.textContent = '...展開完整內容';
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', function () {
    initializeMailSystem();
});

// 頁面卸載時清理
window.addEventListener('beforeunload', function () {
    stopAutoRefresh();
});

// 全域錯誤處理
window.addEventListener('error', (e) => {
    console.error('郵件系統錯誤:', e.error);
});