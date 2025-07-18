class MarketReportSender {
    constructor() {
        this.form = document.getElementById('email-form');
        this.dataStatus = document.getElementById('data-status');
        this.sendBtn = document.getElementById('send-btn');
        this.resultModal = document.getElementById('result-modal');
        this.modalIcon = document.getElementById('modal-icon');
        this.modalTitle = document.getElementById('modal-title');
        this.modalMessage = document.getElementById('modal-message');
        this.modalClose = document.getElementById('modal-close');
        this.statusIndicator = document.getElementById('status-indicator');

        this.init();
    }

    init() {
        this.loadCurrentData();
        this.bindEvents();

        // 每30秒檢查一次資料更新
        setInterval(() => this.loadCurrentData(), 30000);

        // 添加頁面載入動畫
        this.animatePageLoad();
    }

    animatePageLoad() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';

            setTimeout(() => {
                card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 200);
        });
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // 監聽表單變化來啟用/禁用發送按鈕
        const inputs = this.form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.validateForm());
            input.addEventListener('focus', this.handleInputFocus);
            input.addEventListener('blur', this.handleInputBlur);
        });

        // 彈窗關閉事件
        this.modalClose.addEventListener('click', () => this.hideModal());
        this.resultModal.addEventListener('click', (e) => {
            if (e.target === this.resultModal) {
                this.hideModal();
            }
        });

        // ESC 鍵關閉彈窗
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.resultModal.classList.contains('show')) {
                this.hideModal();
            }
        });

        // 複選框動畫
        const checkboxes = document.querySelectorAll('.custom-checkbox input');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleCheckboxChange);
        });
    }

    handleInputFocus(e) {
        e.target.parentElement.classList.add('focused');
    }

    handleInputBlur(e) {
        e.target.parentElement.classList.remove('focused');
    }

    handleCheckboxChange(e) {
        const label = e.target.nextElementSibling;
        if (e.target.checked) {
            label.style.transform = 'scale(1.02)';
            setTimeout(() => {
                label.style.transform = 'scale(1)';
            }, 150);
        }
    }

    async loadCurrentData() {
        try {
            this.updateStatusIndicator('loading', '載入市場資料...');

            const response = await fetch('/api/current-data');
            const result = await response.json();

            if (result.data && Object.keys(result.data).length > 0) {
                this.displayMarketData(result.data);
                this.updateStatusIndicator('connected', '市場資料已更新');
                this.validateForm();
            } else {
                this.displayNoData();
                this.updateStatusIndicator('waiting', '等待市場資料...');
            }
        } catch (error) {
            console.error('載入市場資料失敗:', error);
            this.displayError('無法載入市場資料');
            this.updateStatusIndicator('error', '連接錯誤');
        }
    }

    updateStatusIndicator(status, text) {
        const dot = this.statusIndicator.querySelector('.indicator-dot');
        const textElement = this.statusIndicator.querySelector('.indicator-text');

        // 移除所有狀態類別
        dot.classList.remove('connected', 'error', 'loading');

        // 添加新狀態
        if (status !== 'waiting') {
            dot.classList.add(status);
        }

        textElement.textContent = text;

        // 添加脈衝動畫
        if (status === 'loading') {
            dot.style.animation = 'pulse 1s ease-in-out infinite';
        } else {
            dot.style.animation = 'pulse 2s ease-in-out infinite';
        }
    }

    displayMarketData(data) {
        const sentimentClass = this.getSentimentClass(data.average_sentiment_score);
        const sentimentText = this.getMarketSentimentText(data.average_sentiment_score);
        const sentimentIcon = this.getSentimentIcon(data.average_sentiment_score);

        this.dataStatus.innerHTML = `
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">
                        <i class="fas fa-chart-line"></i>
                        市場情緒指標
                    </div>
                    <div class="data-value">
                        <span class="sentiment-score ${sentimentClass}">
                            <i class="fas ${this.getSentimentFaIcon(data.average_sentiment_score)}"></i>
                            ${data.average_sentiment_score?.toFixed(3)} • ${sentimentText}
                            <span style="margin-left: 0.5rem;">${sentimentIcon}</span>
                        </span>
                    </div>
                </div>
                <div class="data-item">
                    <div class="data-label">
                        <i class="fas fa-calendar-day"></i>
                        報告日期
                    </div>
                    <div class="data-value">${data.market_date || '今日'}</div>
                </div>
                <div class="data-item">
                    <div class="data-label">
                        <i class="fas fa-clock"></i>
                        最後更新
                    </div>
                    <div class="data-value">${data.received_time}</div>
                </div>
                <div class="data-item" style="grid-column: 1 / -1;">
                    <div class="data-label">
                        <i class="fas fa-newspaper"></i>
                        市場分析摘要
                    </div>
                    <div class="message-content">
                        ${this.formatMarketContent(data.message_content)}
                    </div>
                </div>
            </div>
        `;

        // 添加進入動畫
        const items = this.dataStatus.querySelectorAll('.data-item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            setTimeout(() => {
                item.style.transition = 'all 0.4s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    displayNoData() {
        this.dataStatus.innerHTML = `
            <div class="no-data">
                <i class="fas fa-chart-bar"></i>
                <h3>等待今日市場資料</h3>
                <p>請確認 N8N 市場分析工作流程已正確運行</p>
                <div class="pulse-dots" style="margin-top: 1.5rem;">
                    <div class="pulse-dot"></div>
                    <div class="pulse-dot delay-1"></div>
                    <div class="pulse-dot delay-2"></div>
                </div>
            </div>
        `;
        this.sendBtn.disabled = true;
    }

    displayError(message) {
        this.dataStatus.innerHTML = `
            <div class="no-data error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>資料載入失敗</h3>
                <p>${message}</p>
                <button onclick="location.reload()" style="
                    margin-top: 1.5rem;
                    padding: 0.75rem 1.5rem;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: var(--radius);
                    cursor: pointer;
                    font-weight: 600;
                ">重新載入</button>
            </div>
        `;
        this.sendBtn.disabled = true;
    }

    getSentimentClass(score) {
        if (score > 0.1) return 'sentiment-positive';
        if (score < -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    }

    getMarketSentimentText(score) {
        if (score > 0.6) return '極度樂觀';
        if (score > 0.3) return '樂觀';
        if (score > 0.1) return '略為樂觀';
        if (score > -0.1) return '中性';
        if (score > -0.3) return '略為悲觀';
        if (score > -0.6) return '悲觀';
        return '極度悲觀';
    }

    getSentimentIcon(score) {
        if (score > 0.3) return '📈🟢';
        if (score > 0.1) return '📈🔵';
        if (score > -0.1) return '➡️🟡';
        if (score > -0.3) return '📉🟠';
        return '📉🔴';
    }

    getSentimentFaIcon(score) {
        if (score > 0.1) return 'fa-arrow-trend-up';
        if (score < -0.1) return 'fa-arrow-trend-down';
        return 'fa-minus';
    }

    formatMarketContent(content) {
        if (!content) return '無市場分析資料';

        // 如果內容太長，顯示摘要和展開按鈕
        if (content.length > 250) {
            const summary = content.substring(0, 250);
            const remaining = content.substring(250);

            return `
                <span class="market-summary">${summary}</span>
                <span class="market-full" style="display: none;">${remaining}</span>
                <button class="expand-btn" onclick="this.previousElementSibling.style.display='inline'; this.previousElementSibling.previousElementSibling.style.display='none'; this.style.display='none';" 
                        style="
                            margin-left: 0.75rem;
                            padding: 0.5rem 1rem;
                            background: var(--primary);
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-size: 0.85rem;
                            cursor: pointer;
                            font-weight: 500;
                        ">...閱讀完整分析</button>
            `;
        }

        return content;
    }

    validateForm() {
        const email = document.getElementById('recipient_email').value;
        const subject = document.getElementById('subject').value;
        const hasData = !this.dataStatus.innerHTML.includes('no-data');

        const isValid = email && subject && hasData;
        this.sendBtn.disabled = !isValid;

        // 添加視覺反饋
        if (isValid) {
            this.sendBtn.classList.remove('disabled');
        } else {
            this.sendBtn.classList.add('disabled');
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // 添加載入狀態
        this.setLoadingState(true);

        try {
            const formData = new FormData(this.form);
            const emailData = {
                recipient_email: formData.get('recipient_email'),
                subject: formData.get('subject'),
                custom_content: formData.get('custom_content') || '',
                include_sentiment: formData.has('include_sentiment'),
                include_message: formData.has('include_message')
            };

            const response = await fetch('/api/send-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(emailData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showModal('success', '報告發送成功', result.message);
                this.resetForm();
            } else {
                this.showModal('error', '發送失敗', result.detail || '市場報告發送失敗，請稍後再試');
            }

        } catch (error) {
            console.error('發送市場報告失敗:', error);
            this.showModal('error', '網路錯誤', '網路連接失敗，請檢查連接後重試');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        const btnText = this.sendBtn.querySelector('.btn-text');
        const btnIcon = this.sendBtn.querySelector('.btn-icon i');

        if (loading) {
            this.sendBtn.disabled = true;
            this.form.classList.add('loading-state');
            btnText.textContent = '發送中...';
            btnIcon.className = 'fas fa-spinner';
            btnIcon.style.animation = 'spin 1s linear infinite';
        } else {
            this.form.classList.remove('loading-state');
            btnText.textContent = '發送市場報告';
            btnIcon.className = 'fas fa-paper-plane';
            btnIcon.style.animation = '';
            this.validateForm();
        }
    }

    resetForm() {
        this.form.reset();
        // 重新設定預設值
        document.getElementById('subject').value = '今日市場分析報告 - 智能情感評估';
        document.getElementById('include_sentiment').checked = true;
        document.getElementById('include_message').checked = true;

        // 添加重置動畫
        const inputs = this.form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.style.transform = 'scale(0.98)';
            setTimeout(() => {
                input.style.transition = 'transform 0.2s ease';
                input.style.transform = 'scale(1)';
            }, 50);
        });
    }

    showModal(type, title, message) {
        // 設定圖示和樣式
        const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
        this.modalIcon.innerHTML = `<i class="${iconClass}"></i>`;
        this.modalIcon.className = `modal-icon ${type}`;

        // 設定標題和訊息
        this.modalTitle.textContent = title;
        this.modalMessage.textContent = message;

        // 顯示彈窗
        this.resultModal.classList.add('show');

        // 自動關閉 (成功時6秒，錯誤時不自動關閉)
        if (type === 'success') {
            setTimeout(() => {
                this.hideModal();
            }, 6000);
        }

        // 添加顯示動畫
        setTimeout(() => {
            this.resultModal.querySelector('.modal-content').style.transform = 'scale(1) translateY(0)';
        }, 10);
    }

    hideModal() {
        this.resultModal.classList.remove('show');
    }
}

// 初始化應用程式
document.addEventListener('DOMContentLoaded', () => {
    new MarketReportSender();

    // 添加全域樣式改進
    const style = document.createElement('style');
    style.textContent = `
        .pulse-dots {
            display: flex;
            justify-content: center;
            gap: 0.75rem;
        }
        
        .focused {
            transform: scale(1.01);
        }
        
        .disabled {
            opacity: 0.6;
            transform: none !important;
        }
        
        .market-summary {
            display: inline;
        }
        
        .expand-btn:hover {
            background: var(--primary-dark) !important;
            transform: translateY(-1px);
        }
        
        .loading-state {
            pointer-events: none;
            opacity: 0.8;
        }
        
        .error-state {
            border-color: var(--error) !important;
            background: rgba(239, 68, 68, 0.05) !important;
        }
    `;
    document.head.appendChild(style);
});class MailSender {
    constructor() {
        this.form = document.getElementById('email-form');
        this.dataStatus = document.getElementById('data-status');
        this.sendBtn = document.getElementById('send-btn');
        this.resultModal = document.getElementById('result-modal');
        this.modalIcon = document.getElementById('modal-icon');
        this.modalTitle = document.getElementById('modal-title');
        this.modalMessage = document.getElementById('modal-message');
        this.modalClose = document.getElementById('modal-close');
        this.statusIndicator = document.getElementById('status-indicator');

        this.init();
    }

    init() {
        this.loadCurrentData();
        this.bindEvents();

        // 每30秒檢查一次資料更新
        setInterval(() => this.loadCurrentData(), 30000);

        // 添加頁面載入動畫
        this.animatePageLoad();
    }

    animatePageLoad() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';

            setTimeout(() => {
                card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 150);
        });
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // 監聽表單變化來啟用/禁用發送按鈕
        const inputs = this.form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.validateForm());
            input.addEventListener('focus', this.handleInputFocus);
            input.addEventListener('blur', this.handleInputBlur);
        });

        // 彈窗關閉事件
        this.modalClose.addEventListener('click', () => this.hideModal());
        this.resultModal.addEventListener('click', (e) => {
            if (e.target === this.resultModal) {
                this.hideModal();
            }
        });

        // ESC 鍵關閉彈窗
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.resultModal.classList.contains('show')) {
                this.hideModal();
            }
        });

        // 複選框動畫
        const checkboxes = document.querySelectorAll('.custom-checkbox input');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleCheckboxChange);
        });
    }

    handleInputFocus(e) {
        e.target.parentElement.classList.add('focused');
    }

    handleInputBlur(e) {
        e.target.parentElement.classList.remove('focused');
    }

    handleCheckboxChange(e) {
        const label = e.target.nextElementSibling;
        if (e.target.checked) {
            label.style.transform = 'scale(1.02)';
            setTimeout(() => {
                label.style.transform = 'scale(1)';
            }, 150);
        }
    }

    async loadCurrentData() {
        try {
            this.updateStatusIndicator('loading', '載入中...');

            const response = await fetch('/api/current-data');
            const result = await response.json();

            if (result.data && Object.keys(result.data).length > 0) {
                this.displayData(result.data);
                this.updateStatusIndicator('connected', '已連接');
                this.validateForm();
            } else {
                this.displayNoData();
                this.updateStatusIndicator('waiting', '等待資料...');
            }
        } catch (error) {
            console.error('載入資料失敗:', error);
            this.displayError('無法載入資料');
            this.updateStatusIndicator('error', '連接錯誤');
        }
    }

    updateStatusIndicator(status, text) {
        const dot = this.statusIndicator.querySelector('.indicator-dot');
        const textElement = this.statusIndicator.querySelector('.indicator-text');

        // 移除所有狀態類別
        dot.classList.remove('connected', 'error', 'loading');

        // 添加新狀態
        if (status !== 'waiting') {
            dot.classList.add(status);
        }

        textElement.textContent = text;

        // 添加脈衝動畫
        if (status === 'loading') {
            dot.style.animation = 'pulse 1s ease-in-out infinite';
        } else {
            dot.style.animation = 'pulse 2s ease-in-out infinite';
        }
    }

    displayData(data) {
        const sentimentClass = this.getSentimentClass(data.average_sentiment_score);
        const sentimentText = this.getSentimentText(data.average_sentiment_score);

        this.dataStatus.innerHTML = `
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">
                        <i class="fas fa-chart-line"></i>
                        情感分析分數
                    </div>
                    <div class="data-value">
                        <span class="sentiment-score ${sentimentClass}">
                            <i class="fas ${this.getSentimentIcon(data.average_sentiment_score)}"></i>
                            ${data.average_sentiment_score?.toFixed(2)} (${sentimentText})
                        </span>
                    </div>
                </div>
                <div class="data-item">
                    <div class="data-label">
                        <i class="fas fa-clock"></i>
                        接收時間
                    </div>
                    <div class="data-value">${data.received_time}</div>
                </div>
                <div class="data-item" style="grid-column: 1 / -1;">
                    <div class="data-label">
                        <i class="fas fa-comment-alt"></i>
                        訊息內容
                    </div>
                    <div class="message-content">
                        ${this.formatMessageContent(data.message_content)}
                    </div>
                </div>
            </div>
        `;

        // 添加進入動畫
        const items = this.dataStatus.querySelectorAll('.data-item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            setTimeout(() => {
                item.style.transition = 'all 0.4s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    displayNoData() {
        this.dataStatus.innerHTML = `
            <div class="no-data">
                <i class="fas fa-satellite-dish"></i>
                <h3>等待 N8N 傳送資料</h3>
                <p>請確認 N8N 工作流程已正確設定並運行</p>
                <div class="pulse-dots" style="margin-top: 1rem;">
                    <div class="pulse-dot"></div>
                    <div class="pulse-dot delay-1"></div>
                    <div class="pulse-dot delay-2"></div>
                </div>
            </div>
        `;
        this.sendBtn.disabled = true;
    }

    displayError(message) {
        this.dataStatus.innerHTML = `
            <div class="no-data error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>載入失敗</h3>
                <p>${message}</p>
                <button onclick="location.reload()" style="
                    margin-top: 1rem;
                    padding: 0.5rem 1rem;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: var(--radius);
                    cursor: pointer;
                ">重新載入</button>
            </div>
        `;
        this.sendBtn.disabled = true;
    }

    getSentimentClass(score) {
        if (score > 0.1) return 'sentiment-positive';
        if (score < -0.1) return 'sentiment-negative';
        return 'sentiment-neutral';
    }

    getSentimentText(score) {
        if (score > 0.5) return '非常正面';
        if (score > 0.1) return '正面';
        if (score > -0.1) return '中性';
        if (score > -0.5) return '負面';
        return '非常負面';
    }

    getSentimentIcon(score) {
        if (score > 0.1) return 'fa-smile';
        if (score < -0.1) return 'fa-frown';
        return 'fa-meh';
    }

    formatMessageContent(content) {
        if (!content) return '無資料';

        // 如果內容太長，顯示摘要和展開按鈕
        if (content.length > 200) {
            const summary = content.substring(0, 200);
            const remaining = content.substring(200);

            return `
                <span class="message-summary">${summary}</span>
                <span class="message-full" style="display: none;">${remaining}</span>
                <button class="expand-btn" onclick="this.previousElementSibling.style.display='inline'; this.previousElementSibling.previousElementSibling.style.display='none'; this.style.display='none';" 
                        style="
                            margin-left: 0.5rem;
                            padding: 0.25rem 0.5rem;
                            background: var(--primary);
                            color: white;
                            border: none;
                            border-radius: 4px;
                            font-size: 0.75rem;
                            cursor: pointer;
                        ">...展開</button>
            `;
        }

        return content;
    }

    validateForm() {
        const email = document.getElementById('recipient_email').value;
        const subject = document.getElementById('subject').value;
        const hasData = !this.dataStatus.innerHTML.includes('no-data');

        const isValid = email && subject && hasData;
        this.sendBtn.disabled = !isValid;

        // 添加視覺反饋
        if (isValid) {
            this.sendBtn.classList.remove('disabled');
        } else {
            this.sendBtn.classList.add('disabled');
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // 添加載入狀態
        this.setLoadingState(true);

        try {
            const formData = new FormData(this.form);
            const emailData = {
                recipient_email: formData.get('recipient_email'),
                subject: formData.get('subject'),
                custom_content: formData.get('custom_content') || '',
                include_sentiment: formData.has('include_sentiment'),
                include_message: formData.has('include_message')
            };

            const response = await fetch('/api/send-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(emailData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showModal('success', '發送成功', result.message);
                this.resetForm();
            } else {
                this.showModal('error', '發送失敗', result.detail || '發送失敗，請稍後再試');
            }

        } catch (error) {
            console.error('發送郵件失敗:', error);
            this.showModal('error', '網路錯誤', '網路連接失敗，請檢查連接後重試');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        const btnText = this.sendBtn.querySelector('.btn-text');
        const btnIcon = this.sendBtn.querySelector('.btn-icon i');

        if (loading) {
            this.sendBtn.disabled = true;
            this.form.classList.add('loading-state');
            btnText.textContent = '發送中...';
            btnIcon.className = 'fas fa-spinner';
            btnIcon.style.animation = 'spin 1s linear infinite';
        } else {
            this.form.classList.remove('loading-state');
            btnText.textContent = '發送郵件';
            btnIcon.className = 'fas fa-rocket';
            btnIcon.style.animation = '';
            this.validateForm();
        }
    }

    resetForm() {
        this.form.reset();
        // 重新設定預設值
        document.getElementById('subject').value = 'N8N 情感分析報告';
        document.getElementById('include_sentiment').checked = true;
        document.getElementById('include_message').checked = true;

        // 添加重置動畫
        const inputs = this.form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.style.transform = 'scale(0.98)';
            setTimeout(() => {
                input.style.transition = 'transform 0.2s ease';
                input.style.transform = 'scale(1)';
            }, 50);
        });
    }

    showModal(type, title, message) {
        // 設定圖示和樣式
        const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
        this.modalIcon.innerHTML = `<i class="${iconClass}"></i>`;
        this.modalIcon.className = `modal-icon ${type}`;

        // 設定標題和訊息
        this.modalTitle.textContent = title;
        this.modalMessage.textContent = message;

        // 顯示彈窗
        this.resultModal.classList.add('show');

        // 自動關閉 (成功時5秒，錯誤時不自動關閉)
        if (type === 'success') {
            setTimeout(() => {
                this.hideModal();
            }, 5000);
        }

        // 添加顯示動畫
        setTimeout(() => {
            this.resultModal.querySelector('.modal-content').style.transform = 'scale(1) translateY(0)';
        }, 10);
    }

    hideModal() {
        this.resultModal.classList.remove('show');
    }
}

// 初始化應用程式
document.addEventListener('DOMContentLoaded', () => {
    new MailSender();

    // 添加全域樣式改進
    const style = document.createElement('style');
    style.textContent = `
        .pulse-dots {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .focused {
            transform: scale(1.01);
        }
        
        .disabled {
            opacity: 0.6;
            transform: none !important;
        }
    `;
    document.head.appendChild(style);
});