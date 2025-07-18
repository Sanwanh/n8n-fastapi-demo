# 系統配置檔案

# 伺服器配置
SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 8089,
    'debug': True
}

# 發送目標配置
WEBHOOK_CONFIG = {
    'send_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook - Preview',
    'timeout': 30
}

# 郵件模板配置
EMAIL_TEMPLATES = {
    'default_subject': '市場分析報告',
    'report_header': '=== 市場分析報告 ===',
    'report_footer': '--- 報告結束 ---'
}

# 情感分析配置
SENTIMENT_CONFIG = {
    'thresholds': {
        'very_positive': 0.5,
        'positive': 0.1,
        'neutral_upper': 0.1,
        'neutral_lower': -0.1,
        'negative': -0.5
    },
    'labels': {
        'very_positive': '正面',
        'positive': '中性偏正', 
        'neutral': '中性',
        'negative': '中性偏負',
        'very_negative': '負面'
    }
}

# 系統資訊
SYSTEM_INFO = {
    'name': 'Market Analysis Report System',
    'version': '1.0.0',
    'description': '市場分析報告發送系統'
}

# 注意事項:
# 1. 此版本不需要 Gmail 設定，因為只是將資料轉發
# 2. send_url 是您要發送資料的目標 URL
# 3. 如果您的 ngrok URL 改變，請更新 WEBHOOK_CONFIG['send_url']