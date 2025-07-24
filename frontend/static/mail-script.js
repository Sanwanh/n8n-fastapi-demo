// 郵件發送系統 JavaScript - 完整版
console.log('📧 郵件發送系統載入中...');

// 全域變數
let currentMarketData = null;
let currentStep = 1;
let formValid = false;

// 時間更新
function updateSystemTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString('zh-TW');
}

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    loadMarketData();
    bindEvents();
    updateSystemTime();
    setInterval(updateSystemTime, 1000);

    // 自動填充今日日期到主題
    const today = new Date().toLocaleDateString('zh-TW');
    const subjectInput = document.getElementById('subject');
    if (subjectInput.value === '市場分析報告') {
        subjectInput.value = `市場分析報告 - ${today}`;
    }

    console.log('✅ 郵件系統初始化完成');
});

// 綁定事件
function bindEvents() {
    // 表單提交
    document.getElementById('mail-form').addEventListener('submit', handleSubmit);

    // 模態框關閉
    document.getElementById('result-close').addEventListener('click', hideModal);
    document.getElementById('result-ok').addEventListener('click', hideModal);
    document.getElementById('send-another').addEventListener('click', () => {
        hideModal();
        resetForm();
    });

    // 表單驗證
    const requiredInputs = document.querySelectorAll('#mail-form input[required]');
    requiredInputs.forEach(input => {
        input.addEventListener('input', validateCurrentStep);
        input.addEventListener('blur', validateCurrentStep);
    });

    // 步驟導航
    document.getElementById('next-btn').addEventListener('click', nextStep);
    document.getElementById('prev-btn').addEventListener('click', prevStep);

    // 即時預覽
    document.querySelectorAll('#mail-form input, #mail-form textarea, #mail-form select').forEach(input => {
        input.addEventListener('input', debounce(generatePreview, 500));
    });

    // 模態框外部點擊關閉
    document.getElementById('result-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) hideModal();
    });

    // ESC 鍵關閉模態框
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') hideModal();
    });
}

// 載入市場數據
async function loadMarketData() {
    try {
        updateStatus('loading', '載入市場數據...');

        const response = await fetch('/api/current-data');
        const result = await response.json();

        if (result.data && Object.keys(result.data).length > 0) {
            currentMarketData = result.data;
            displayMarketData(result.data);
            updateStatus('connected', '數據已更新');

            // 更新最後更新時間
            document.getElementById('last-updated').querySelector('span').textContent =
                `數據更新: ${result.data.received_time}`;

            validateCurrentStep();
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

// 顯示市場數據（郵件頁面專用 - 精簡版）
function displayMarketData(data) {
    const sentimentClass = getSentimentClass(data.average_sentiment_score);
    const sentimentText = getSentimentText(data.average_sentiment_score);

    document.getElementById('market-data-display').innerHTML = `
        <div class="market-data-preview">
            <div class="preview-header">
                <h4><i class="fas fa-chart-pulse"></i> 將發送的市場數據預覽</h4>
                <div class="data-freshness">
                    <i class="fas fa-clock"></i>
                    <span>數據時間: ${data.received_time}</span>
                </div>
            </div>

            <div class="data-summary">
                <div class="summary-card sentiment-${sentimentClass}">
                    <div class="summary-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-label">市場情緒</div>
                        <div class="summary-value">${sentimentText}</div>
                        <div class="summary-score">${data.average_sentiment_score?.toFixed(3)}</div>
                    </div>
                </div>

                <div class="summary-card">
                    <div class="summary-icon">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <div class="summary-content">
                        <div class="summary-label">分析日期</div>
                        <div class="summary-value">${data.market_date || '今日'}</div>
                    </div>
                </div>


            </div>

            <div class="content-preview">
                <h5><i class="fas fa-newspaper"></i> 分析內容摘要</h5>
                <div class="content-snippet">
                    ${formatContentPreview(data.message_content)}
                </div>
                <div class="content-stats">
                    <span class="stat"><i class="fas fa-file-alt"></i> ${data.message_content?.length || 0} 字元</span>
                    <span class="stat"><i class="fas fa-language"></i> 繁體中文</span>
                </div>
            </div>

            <div class="preview-footer">
                <div class="data-quality">
                    <i class="fas fa-check-circle"></i>
                    <span>資料完整，可以發送</span>
                </div>
            </div>
        </div>
    `;
}

// 表單步驟控制
function nextStep() {
    if (!validateCurrentStep()) return;

    if (currentStep < 4) {
        currentStep++;
        showStep(currentStep);
        if (currentStep === 4) {
            generatePreview();
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
    }
}

function showStep(step) {
    // 隱藏所有步驟
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.progress-step').forEach(s => s.classList.remove('active'));

    // 顯示當前步驟
    document.querySelector(`.form-step[data-step="${step}"]`).classList.add('active');
    document.querySelector(`.progress-step[data-step="${step}"]`).classList.add('active');

    // 更新導航按鈕
    document.getElementById('prev-btn').style.display = step > 1 ? 'flex' : 'none';
    document.getElementById('next-btn').style.display = step < 4 ? 'flex' : 'none';
    document.getElementById('send-btn').style.display = step === 4 ? 'flex' : 'none';

    // 更新步驟計數器
    document.querySelector('.step-current').textContent = step;

    validateCurrentStep();
}

// 表單驗證
function validateCurrentStep() {
    let isValid = true;

    if (currentStep === 1) {
        const recipient = document.getElementById('recipient').value;
        isValid = recipient && recipient.includes('@') && currentMarketData;
    } else if (currentStep === 2) {
        const subject = document.getElementById('subject').value;
        isValid = subject.trim().length > 0;
    }

    // 更新按鈕狀態
    document.getElementById('next-btn').disabled = !isValid;
    document.getElementById('send-btn').disabled = !isValid;

    return isValid;
}

// 生成郵件預覽
function generatePreview() {
    if (!currentMarketData) {
        document.getElementById('preview-content').innerHTML = '<p class="error">無市場數據可預覽</p>';
        return;
    }

    const formData = new FormData(document.getElementById('mail-form'));
    const content = generateEmailContent(formData);

    document.getElementById('preview-content').innerHTML = `
        <div class="email-preview-content">
            <div class="preview-meta">
                <div class="meta-item">
                    <strong>收件人:</strong> ${formData.get('recipient')}
                </div>
                <div class="meta-item">
                    <strong>主旨:</strong> ${formData.get('subject')}
                </div>
                <div class="meta-item">
                    <strong>優先級:</strong> ${getPriorityText(formData.get('priority'))}
                </div>
            </div>
            <div class="preview-divider"></div>
            <div class="preview-body">
                <pre class="email-content">${content}</pre>
            </div>
        </div>
    `;
}

// 生成郵件內容
function generateEmailContent(formData) {
    const customMessage = formData.get('custom_message') || '';
    const includeCharts = formData.has('include_charts');
    const includeRecommendations = formData.has('include_recommendations');
    const includeRiskWarning = formData.has('include_risk_warning');

    let content = '';

    // 自訂開頭訊息
    if (customMessage.trim()) {
        content += `${customMessage}\n\n`;
    }

    // 郵件標題
    content += `╔══════════════════════════════════════════╗\n`;
    content += `║              📊 市場分析報告 📊           ║\n`;
    content += `╚══════════════════════════════════════════╝\n\n`;

    // 基本資訊
    content += `📅 報告日期：${currentMarketData.market_date || '今日'}\n`;
    content += `⏰ 生成時間：${new Date().toLocaleString('zh-TW')}\n`;
    content += `📡 數據來源：N8N 市場分析系統\n\n`;

    // 市場概況
    content += `📊 市場概況分析\n`;
    content += `${'─'.repeat(40)}\n`;
    content += `💹 情感分析分數：${currentMarketData.average_sentiment_score?.toFixed(3)}\n`;
    content += `📈 情感評估：${getSentimentText(currentMarketData.average_sentiment_score)}\n\n`;

    // 詳細分析
    if (currentMarketData.message_content) {
        content += `📰 詳細市場分析\n`;
        content += `${'─'.repeat(40)}\n`;
        content += `${currentMarketData.message_content}\n\n`;
    }

    // 可選內容
    if (includeCharts) {
        content += `📊 圖表分析：本報告包含相關市場圖表分析\n`;
    }

    if (includeRecommendations) {
        content += `💡 投資建議：基於當前分析提供相應投資建議\n`;
    }

    if (includeRiskWarning) {
        content += `⚠️  風險提醒：請注意市場風險，謹慎投資決策\n`;
    }

    content += `\n`;

    // 系統資訊
    content += `${'─'.repeat(50)}\n`;
    content += `🤖 本報告由智能市場分析系統自動生成\n`;
    content += `📧 發送系統：市場分析郵件系統 v2.1\n`;
    content += `⏱️  數據接收時間：${currentMarketData.received_time}\n`;
    content += `📞 如有疑問，請聯繫系統管理員\n`;
    content += `${'─'.repeat(50)}\n`;

    return content;
}

// 處理表單提交
async function handleSubmit(e) {
    e.preventDefault();

    if (!currentMarketData) {
        showModal('error', '發送失敗', '沒有可用的市場數據');
        return;
    }

    setLoadingState(true);

    try {
        const formData = new FormData(e.target);
        const mailData = {
            recipient_email: formData.get('recipient'),
            sender_name: formData.get('sender_name') || '市場分析系統',
            subject: formData.get('subject'),
            priority: formData.get('priority') || 'normal',
            mail_type: formData.get('mail_type') || 'daily',
            custom_message: formData.get('custom_message') || '',
            include_charts: formData.has('include_charts'),
            include_recommendations: formData.has('include_recommendations'),
            include_risk_warning: formData.has('include_risk_warning')
        };

        const response = await fetch('/api/send-mail-to-n8n', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mailData)
        });

        const result = await response.json();

        if (response.ok) {
            showModal('success', '發送成功',
                `郵件已成功發送至 ${formData.get('recipient')}`,
                `發送時間: ${result.sent_time}`);
        } else {
            throw new Error(result.detail || '發送失敗');
        }

    } catch (error) {
        console.error('發送郵件失敗:', error);

        let errorMessage = '網路連接失敗，請檢查連接後重試';
        if (error.message.includes('Failed to fetch')) {
            errorMessage = '無法連接到 N8N 服務，請檢查 webhook URL 是否正確';
        } else if (error.message.includes('HTTP')) {
            errorMessage = `伺服器回應錯誤：${error.message}`;
        }

        showModal('error', '發送失敗', errorMessage);
    } finally {
        setLoadingState(false);
    }
}

// 輔助函數
function updateStatus(status, text) {
    const dot = document.querySelector('#status-indicator .indicator-dot');
    const textElement = document.querySelector('#status-indicator .indicator-text');

    dot.classList.remove('connected', 'error', 'loading');
    if (status !== 'waiting') {
        dot.classList.add(status);
    }
    textElement.textContent = text;
}

function displayNoData() {
    document.getElementById('market-data-display').innerHTML = `
        <div class="no-data">
            <i class="fas fa-chart-bar"></i>
            <h3>等待市場數據</h3>
            <p>請確認 N8N 工作流程已正確運行並發送數據</p>
            <button onclick="loadMarketData()" class="retry-btn">
                <i class="fas fa-refresh"></i>
                重新載入
            </button>
        </div>
    `;
}

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

function getSentimentClass(score) {
    if (score > 0.1) return 'positive';
    if (score < -0.1) return 'negative';
    return 'neutral';
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

function formatContentPreview(content) {
    if (!content) return '無市場分析內容';
    if (content.length > 200) {
        return content.substring(0, 200) + '...';
    }
    return content;
}

function getPriorityText(priority) {
    const priorities = {
        'low': '低優先級',
        'normal': '一般',
        'high': '高優先級'
    };
    return priorities[priority] || '一般';
}

function setLoadingState(loading) {
    const sendBtn = document.getElementById('send-btn');
    if (loading) {
        sendBtn.classList.add('loading');
        sendBtn.disabled = true;
    } else {
        sendBtn.classList.remove('loading');
        validateCurrentStep();
    }
}

function showModal(type, title, message, details = '') {
    const modal = document.getElementById('result-modal');
    const icon = document.getElementById('result-icon');
    const titleEl = document.getElementById('result-title');
    const messageEl = document.getElementById('result-message');
    const detailsEl = document.getElementById('result-details');

    icon.className = `modal-icon ${type}`;
    icon.innerHTML = type === 'success' ?
        '<i class="fas fa-check-circle"></i>' :
        '<i class="fas fa-exclamation-circle"></i>';

    titleEl.textContent = title;
    messageEl.textContent = message;
    detailsEl.textContent = details;

    modal.classList.add('show');

    // 成功時自動關閉
    if (type === 'success') {
        setTimeout(() => {
            hideModal();
        }, 5000);
    }
}

function hideModal() {
    document.getElementById('result-modal').classList.remove('show');
}

function resetForm() {
    currentStep = 1;
    showStep(1);
    document.getElementById('mail-form').reset();

    // 重新設定預設值
    const today = new Date().toLocaleDateString('zh-TW');
    document.getElementById('subject').value = `市場分析報告 - ${today}`;
    document.getElementById('sender_name').value = '市場分析系統';
    document.getElementById('priority_normal').checked = true;

    validateCurrentStep();
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 全域錯誤處理
window.addEventListener('error', (e) => {
    console.error('全域錯誤:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('未處理的 Promise 拒絕:', e.reason);
});

