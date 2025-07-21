class MailSender {
    constructor() {
        this.currentMarketData = null;
        this.initializeElements();
        this.bindEvents();
        this.loadMarketData();
        this.initializeForm();
    }

    initializeElements() {
        // 表單元素
        this.mailForm = document.getElementById('mail-form');
        this.sendBtn = document.getElementById('send-btn');
        this.previewBtn = document.getElementById('preview-btn');

        // 狀態顯示
        this.statusIndicator = document.getElementById('status-indicator');
        this.marketDataDisplay = document.getElementById('market-data-display');

        // 模態框
        this.previewModal = document.getElementById('preview-modal');
        this.resultModal = document.getElementById('result-modal');
        this.previewClose = document.getElementById('preview-close');
        this.resultClose = document.getElementById('result-close');
        this.previewCancel = document.getElementById('preview-cancel');
        this.previewSend = document.getElementById('preview-send');
        this.resultOk = document.getElementById('result-ok');

        // 預覽相關
        this.emailPreview = document.getElementById('email-preview');
        this.resultIcon = document.getElementById('result-icon');
        this.resultTitle = document.getElementById('result-title');
        this.resultMessage = document.getElementById('result-message');
        this.resultDetails = document.getElementById('result-details');
    }

    bindEvents() {
        // 表單事件
        this.mailForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.previewBtn.addEventListener('click', () => this.showPreview());

        // 模態框事件
        this.previewClose.addEventListener('click', () => this.hidePreview());
        this.previewCancel.addEventListener('click', () => this.hidePreview());
        this.previewSend.addEventListener('click', () => this.confirmSend());
        this.resultClose.addEventListener('click', () => this.hideResult());
        this.resultOk.addEventListener('click', () => this.hideResult());

        // 點擊外部關閉模態框
        this.previewModal.addEventListener('click', (e) => {
            if (e.target === this.previewModal) this.hidePreview();
        });
        this.resultModal.addEventListener('click', (e) => {
            if (e.target === this.resultModal) this.hideResult();
        });

        // ESC 鍵關閉模態框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hidePreview();
                this.hideResult();
            }
        });

        // 表單驗證
        const inputs = this.mailForm.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.validateForm());
        });

        // 主旨自動填充日期
        const subjectInput = document.getElementById('subject');
        if (subjectInput.value.includes('{date}')) {
            const today = new Date().toLocaleDateString('zh-TW');
            subjectInput.value = subjectInput.value.replace('{date}', today);
        }
    }

    async loadMarketData() {
        try {
            this.updateStatus('loading', '載入市場數據...');

            const response = await fetch('/api/current-data');
            const result = await response.json();

            if (result.data && Object.keys(result.data).length > 0) {
                this.currentMarketData = result.data;
                this.displayMarketData(result.data);
                this.updateStatus('connected', '市場數據已更新');
                this.validateForm();
            } else {
                this.displayNoData();
                this.updateStatus('waiting', '等待市場數據...');
            }

        } catch (error) {
            console.error('載入市場數據失敗:', error);
            this.displayError('無法載入市場數據: ' + error.message);
            this.updateStatus('error', '連接錯誤');
        }
    }

    updateStatus(status, text) {
        const dot = this.statusIndicator.querySelector('.indicator-dot');
        const textElement = this.statusIndicator.querySelector('.indicator-text');

        dot.classList.remove('connected', 'error', 'loading');
        if (status !== 'waiting') {
            dot.classList.add(status);
        }

        textElement.textContent = text;
    }

    displayMarketData(data) {
        const sentimentClass = this.getSentimentClass(data.average_sentiment_score);
        const sentimentText = this.getSentimentText(data.average_sentiment_score);

        this.marketDataDisplay.innerHTML = `
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
                
                <div class="data-row">
                    <div class="data-label">
                        <i class="fas fa-trending-up"></i>
                        趋势方向
                    </div>
                    <div class="data-value">${data.trend_direction || '未知'}</div>
                </div>
                
                <div class="data-row">
                    <div class="data-label">
                        <i class="fas fa-star"></i>
                        信心水平
                    </div>
                    <div class="data-value">${data.confidence_level || '未知'}</div>
                </div>
                
                <div style="grid-column: 1 / -1;">
                    <div class="data-label" style="margin-bottom: 1rem;">
                        <i class="fas fa-newspaper"></i>
                        市場分析內容
                    </div>
                    <div class="market-content">
                        ${this.formatContent(data.message_content)}
                    </div>
                </div>
            </div>
        `;
    }

    displayNoData() {
        this.marketDataDisplay.innerHTML = `
            <div class="no-data">
                <i class="fas fa-chart-bar"></i>
                <h3>等待市場數據</h3>
                <p>請確認 N8N 工作流程已正確運行並發送數據</p>
            </div>
        `;
        this.sendBtn.disabled = true;
        this.previewBtn.disabled = true;
    }

    displayError(message) {
        this.marketDataDisplay.innerHTML = `
            <div class="no-data error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>數據載入失敗</h3>
                <p>${message}</p>
                <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                    <i class="fas fa-refresh"></i>
                    重新載入
                </button>
            </div>
        `;
        this.sendBtn.disabled = true;
        this.previewBtn.disabled = true;
    }

    getSentimentClass(score) {
        if (score > 0.1) return 'sentiment-positive';
        if (score < -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    }

    getSentimentText(score) {
        if (score > 0.6) return '極度樂觀';
        if (score > 0.3) return '樂觀';
        if (score > 0.1) return '略為樂觀';
        if (score > -0.1) return '中性';
        if (score > -0.3) return '略為悲觀';
        if (score > -0.6) return '悲觀';
        return '極度悲觀';
    }

    formatContent(content) {
        if (!content) return '無市場分析內容';

        if (content.length > 300) {
            const preview = content.substring(0, 300);
            const remaining = content.substring(300);

            return `
                <span class="content-preview">${preview}</span>
                <span class="content-full" style="display: none;">${remaining}</span>
                <button class="expand-btn" onclick="this.previousElementSibling.style.display='inline'; this.previousElementSibling.previousElementSibling.style.display='none'; this.style.display='none';"
                        style="margin-left: 1rem; padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer;">
                    ...展開完整內容
                </button>
            `;
        }

        return content;
    }

    initializeForm() {
        // 設置預設值
        const today = new Date().toLocaleDateString('zh-TW');
        const subjectInput = document.getElementById('subject');
        if (subjectInput.value.includes('{date}')) {
            subjectInput.value = subjectInput.value.replace('{date}', today);
        }
    }

    validateForm() {
        const recipient = document.getElementById('recipient').value;
        const subject = document.getElementById('subject').value;
        const hasData = this.currentMarketData !== null;

        const isValid = recipient && subject && hasData;
        this.sendBtn.disabled = !isValid;
        this.previewBtn.disabled = !isValid;

        if (isValid) {
            this.sendBtn.classList.remove('error-state');
            this.previewBtn.classList.remove('error-state');
        }
    }

    generateEmailContent() {
        const formData = new FormData(this.mailForm);
        const customMessage = formData.get('custom_message') || '';

        let content = '';

        // 自訂訊息
        if (customMessage.trim()) {
            content += `${customMessage}\n\n`;
        }

        // 郵件標題
        content += `╔══════════════════════════════════════════╗\n`;
        content += `║              📊 市場分析報告 📊           ║\n`;
        content += `╚══════════════════════════════════════════╝\n\n`;

        // 基本信息
        content += `📅 報告日期：${this.currentMarketData.market_date || '今日'}\n`;
        content += `⏰ 生成時間：${new Date().toLocaleString('zh-TW')}\n`;
        content += `📡 數據來源：N8N 市場分析系統\n\n`;

        // 市場概況
        content += `📊 市場概況分析\n`;
        content += `${'─'.repeat(40)}\n`;
        content += `💹 情感分析分數：${this.currentMarketData.average_sentiment_score?.toFixed(3)}\n`;
        content += `📈 情感評估：${this.getSentimentText(this.currentMarketData.average_sentiment_score)}\n`;
        content += `🎯 信心水平：${this.currentMarketData.confidence_level || '未知'}\n`;
        content += `📊 趨勢方向：${this.currentMarketData.trend_direction || '未知'}\n`;
        content += `🛡️  風險評估：${this.currentMarketData.risk_assessment || '未知'}\n\n`;

        // 詳細分析
        if (this.currentMarketData.message_content) {
            content += `📰 詳細市場分析\n`;
            content += `${'─'.repeat(40)}\n`;
            content += `${this.currentMarketData.message_content}\n\n`;
        }

        // 可選內容
        if (formData.has('include_charts')) {
            content += `📊 圖表分析：本報告包含相關市場圖表分析\n`;
        }

        if (formData.has('include_recommendations')) {
            content += `💡 投資建議：基於當前分析提供相應投資建議\n`;
        }

        if (formData.has('include_risk_warning')) {
            content += `⚠️  風險提醒：請注意市場風險，謹慎投資決策\n`;
        }

        content += `\n`;

        // 系統信息
        content += `${'─'.repeat(50)}\n`;
        content += `🤖 本報告由智能市場分析系統自動生成\n`;
        content += `📧 發送系統：市場分析郵件系統 v2.0\n`;
        content += `⏱️  數據接收時間：${this.currentMarketData.received_time}\n`;
        content += `📞 如有疑問，請聯繫系統管理員\n`;
        content += `${'─'.repeat(50)}\n`;

        return content;
    }

    showPreview() {
        const emailContent = this.generateEmailContent();
        this.emailPreview.textContent = emailContent;
        this.previewModal.classList.add('show');
    }

    hidePreview() {
        this.previewModal.classList.remove('show');
    }

    confirmSend() {
        this.hidePreview();
        this.sendEmail();
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.sendEmail();
    }

    async sendEmail() {
        if (!this.currentMarketData) {
            this.showResult('error', '發送失敗', '沒有可用的市場數據');
            return;
        }

        this.setLoadingState(true);

        try {
            const formData = new FormData(this.mailForm);

            // 構建要發送到 N8N 的數據結構
            const emailData = {
                // 原始 N8N 數據
                ...this.currentMarketData,

                // 郵件相關信息
                recipient_email: formData.get('recipient'),
                sender_name: formData.get('sender_name') || '市場分析系統',
                subject: formData.get('subject'),
                priority: formData.get('priority') || 'normal',
                mail_type: formData.get('mail_type') || 'daily',
                custom_message: formData.get('custom_message') || '',

                // 選項設定
                include_charts: formData.has('include_charts'),
                include_recommendations: formData.has('include_recommendations'),
                include_risk_warning: formData.has('include_risk_warning'),

                // 生成的郵件內容
                email_content: this.generateEmailContent(),

                // 系統信息
                send_timestamp: new Date().toISOString(),
                system_version: '2.0',
                source: 'mail-sender-page'
            };

            // 發送到指定的 N8N webhook
            const response = await fetch('https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook%20-%20Preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(emailData)
            });

            if (response.ok) {
                const result = await response.text(); // 可能返回文字而不是 JSON

                this.showResult('success', '發送成功',
                    `郵件已成功發送至 ${formData.get('recipient')}`);

                // 重置表單
                this.resetForm();

            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

        } catch (error) {
            console.error('發送郵件失敗:', error);

            let errorMessage = '網路連接失敗，請檢查連接後重試';
            if (error.message.includes('Failed to fetch')) {
                errorMessage = '無法連接到 N8N 服務，請檢查 webhook URL 是否正確';
            } else if (error.message.includes('HTTP')) {
                errorMessage = `伺服器回應錯誤：${error.message}`;
            }

            this.showResult('error', '發送失敗', errorMessage);
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        if (loading) {
            this.sendBtn.classList.add('loading');
            this.sendBtn.disabled = true;
        } else {
            this.sendBtn.classList.remove('loading');
            this.validateForm();
        }
    }

    showResult(type, title, message, details = '') {
        this.resultIcon.className = `modal-icon ${type}`;
        this.resultIcon.innerHTML = type === 'success' ?
            '<i class="fas fa-check-circle"></i>' :
            '<i class="fas fa-exclamation-circle"></i>';

        this.resultTitle.textContent = title;
        this.resultMessage.textContent = message;
        this.resultDetails.textContent = details;

        this.resultModal.classList.add('show');

        // 成功時自動關閉
        if (type === 'success') {
            setTimeout(() => {
                this.hideResult();
            }, 5000);
        }
    }

    hideResult() {
        this.resultModal.classList.remove('show');
    }

    resetForm() {
        // 保留一些基本信息，清空其他字段
        document.getElementById('custom_message').value = '';

        // 重新設置今日日期
        const today = new Date().toLocaleDateString('zh-TW');
        const subjectInput = document.getElementById('subject');
        if (subjectInput.value.includes(today)) {
            // 如果已經包含今日日期，不做更改
        } else {
            subjectInput.value = `市場分析報告 - ${today}`;
        }

        // 可以選擇性地保留收件人信息
        // document.getElementById('recipient').value = '';
    }
}

// 初始化應用
document.addEventListener('DOMContentLoaded', () => {
    new MailSender();

    // 每30秒自動刷新市場數據
    setInterval(() => {
        if (window.mailSender) {
            window.mailSender.loadMarketData();
        }
    }, 30000);
});

// 全局錯誤處理
window.addEventListener('error', (e) => {
    console.error('全局錯誤:', e.error);
});

// 全局未處理的 Promise 拒絕
window.addEventListener('unhandledrejection', (e) => {
    console.error('未處理的 Promise 拒絕:', e.reason);
});