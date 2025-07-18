"""
市場分析報告系統 - 配置檔案
Market Analysis Report System - Configuration File

此檔案包含系統的所有配置設定
請根據您的需求調整這些設定值
"""

import os
from datetime import datetime

# ================================
# 伺服器配置 Server Configuration
# ================================
SERVER_CONFIG = {
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),  # 伺服器綁定位址
    'port': int(os.getenv('SERVER_PORT', 8089)),  # 伺服器端口
    'debug': os.getenv('DEBUG', 'True').lower() == 'true',  # 除錯模式
    'reload': True,  # 自動重載（僅開發模式）
    'workers': 1,  # 工作進程數
    'log_level': os.getenv('LOG_LEVEL', 'info')  # 日誌級別
}

# ================================
# Webhook 配置 Webhook Configuration
# ================================
WEBHOOK_CONFIG = {
    # 主要發送目標 URL - 請根據您的 ngrok 或實際部署調整
    'send_url': os.getenv(
        'WEBHOOK_URL',
        'https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2'
    ),

    # 備用 URL（如果主要 URL 失敗）
    'backup_url': os.getenv('BACKUP_WEBHOOK_URL', ''),

    # 請求超時時間（秒）
    'timeout': int(os.getenv('WEBHOOK_TIMEOUT', 30)),

    # 重試配置
    'retry_attempts': 3,  # 最大重試次數
    'retry_delay': 2,  # 重試間隔（秒）

    # 請求標頭
    'headers': {
        'User-Agent': 'Market-Analysis-System/1.0',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-System-Version': '1.0.0'
    }
}

# ================================
# 郵件範本配置 Email Template Configuration
# ================================
EMAIL_TEMPLATES = {
    # 預設主題
    'default_subject': os.getenv('DEFAULT_EMAIL_SUBJECT', '市場分析報告'),

    # 郵件範本
    'report_header': '╔══════════════════════════════════════════╗\n║          📊 市場分析報告 📊          ║\n╚══════════════════════════════════════════╝',
    'report_footer': '╔══════════════════════════════════════════╗\n║     本報告由智能分析系統自動生成     ║\n║        感謝您使用我們的服務！        ║\n╚══════════════════════════════════════════╝',

    # 分段標題
    'section_divider': '─' * 50,
    'subsection_divider': '·' * 30,

    # 系統簽名
    'system_signature': '🤖 市場分析報告系統 | 智能分析 • 精準決策',

    # 不同類型的報告範本
    'templates': {
        'daily': {
            'subject': '每日市場分析報告 - {date}',
            'greeting': '📅 每日市場分析報告',
            'intro': '以下是今日的市場分析摘要，請查收：'
        },
        'weekly': {
            'subject': '週度市場分析報告 - {date}',
            'greeting': '📊 週度市場分析報告',
            'intro': '以下是本週的市場分析總結，請查收：'
        },
        'alert': {
            'subject': '⚠️ 市場警示報告 - {date}',
            'greeting': '🚨 重要市場警示',
            'intro': '檢測到重要市場變化，請立即查看：'
        }
    }
}

# ================================
# 情感分析配置 Sentiment Analysis Configuration
# ================================
SENTIMENT_CONFIG = {
    # 情感分數閾值
    'thresholds': {
        'very_positive': float(os.getenv('SENTIMENT_VERY_POSITIVE', 0.6)),  # 極度正面
        'positive': float(os.getenv('SENTIMENT_POSITIVE', 0.2)),  # 正面
        'neutral_upper': float(os.getenv('SENTIMENT_NEUTRAL_UPPER', 0.1)),  # 中性上限
        'neutral_lower': float(os.getenv('SENTIMENT_NEUTRAL_LOWER', -0.1)),  # 中性下限
        'negative': float(os.getenv('SENTIMENT_NEGATIVE', -0.2)),  # 負面
        'very_negative': float(os.getenv('SENTIMENT_VERY_NEGATIVE', -0.6))  # 極度負面
    },

    # 情感標籤
    'labels': {
        'very_positive': '極度樂觀',
        'positive': '樂觀',
        'neutral_positive': '中性偏樂觀',
        'neutral': '中性',
        'neutral_negative': '中性偏悲觀',
        'negative': '悲觀',
        'very_negative': '極度悲觀'
    },

    # 情感顏色代碼（用於前端顯示）
    'colors': {
        'very_positive': '#10b981',  # 綠色
        'positive': '#059669',  # 深綠色
        'neutral_positive': '#f59e0b',  # 黃色
        'neutral': '#6b7280',  # 灰色
        'neutral_negative': '#f59e0b',  # 黃色
        'negative': '#ef4444',  # 紅色
        'very_negative': '#dc2626'  # 深紅色
    },

    # 市場表情符號
    'emojis': {
        'very_positive': '🚀📈💚',
        'positive': '📈🟢😊',
        'neutral_positive': '📊🟡😐',
        'neutral': '➡️⚪😑',
        'neutral_negative': '📊🟡😐',
        'negative': '📉🔴😟',
        'very_negative': '💥📉😱'
    }
}

# ================================
# 資料處理配置 Data Processing Configuration
# ================================
DATA_CONFIG = {
    # 資料保存配置
    'max_stored_reports': int(os.getenv('MAX_STORED_REPORTS', 100)),  # 最大儲存報告數
    'data_retention_days': int(os.getenv('DATA_RETENTION_DAYS', 30)),  # 資料保留天數
    'auto_cleanup': os.getenv('AUTO_CLEANUP', 'True').lower() == 'true',  # 自動清理

    # 內容處理
    'max_content_length': int(os.getenv('MAX_CONTENT_LENGTH', 10000)),  # 最大內容長度
    'content_preview_length': 200,  # 內容預覽長度
    'enable_content_summary': True,  # 啟用內容摘要

    # 資料驗證
    'require_sentiment_score': True,  # 需要情感分數
    'sentiment_score_range': (-1.0, 1.0),  # 情感分數範圍
    'require_message_content': True  # 需要訊息內容
}

# ================================
# 系統資訊 System Information
# ================================
SYSTEM_INFO = {
    'name': 'Market Analysis Report System',
    'version': '1.2.0',
    'description': '智能市場分析報告發送系統',
    'author': 'AI Development Team',
    'contact': 'support@example.com',
    'documentation': 'https://docs.example.com/market-analysis',
    'build_date': datetime.now().strftime('%Y-%m-%d'),

    # 功能特性
    'features': [
        '即時市場情感分析',
        'N8N 工作流程整合',
        '自動化報告生成',
        'Webhook 資料轉發',
        '響應式網頁介面',
        'Docker 容器化部署'
    ],

    # 技術規格
    'tech_stack': {
        'backend': 'FastAPI + Python 3.11',
        'frontend': 'HTML5 + CSS3 + JavaScript',
        'deployment': 'Docker + ngrok',
        'integration': 'N8N Workflow'
    }
}

# ================================
# 安全配置 Security Configuration
# ================================
SECURITY_CONFIG = {
    # API 安全
    'enable_api_key': os.getenv('ENABLE_API_KEY', 'False').lower() == 'true',
    'api_key': os.getenv('API_KEY', ''),

    # CORS 設定
    'cors_origins': os.getenv('CORS_ORIGINS', '*').split(','),
    'cors_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'cors_headers': ['*'],

    # 速率限制
    'enable_rate_limit': False,
    'rate_limit_requests': 100,  # 每分鐘請求數
    'rate_limit_window': 60,  # 時間窗口（秒）

    # 資料加密
    'encrypt_stored_data': False,
    'encryption_key': os.getenv('ENCRYPTION_KEY', '')
}

# ================================
# 日誌配置 Logging Configuration
# ================================
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': os.getenv('LOG_FILE_PATH', 'logs/market_analysis.log'),
    'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', 10485760)),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
    'enable_console_log': True,
    'enable_file_log': True
}

# ================================
# 監控配置 Monitoring Configuration
# ================================
MONITORING_CONFIG = {
    # 健康檢查
    'health_check_interval': 30,  # 秒
    'health_check_timeout': 10,  # 秒

    # 效能監控
    'enable_metrics': True,
    'metrics_interval': 60,  # 秒

    # 警示設定
    'enable_alerts': False,
    'alert_email': os.getenv('ALERT_EMAIL', ''),
    'alert_webhook': os.getenv('ALERT_WEBHOOK', ''),

    # 統計資料
    'enable_stats': True,
    'stats_retention_days': 7
}

# ================================
# 開發配置 Development Configuration
# ================================
DEVELOPMENT_CONFIG = {
    # 除錯選項
    'debug_mode': os.getenv('DEBUG', 'True').lower() == 'true',
    'verbose_logging': True,
    'enable_auto_reload': True,

    # 測試資料
    'use_mock_data': os.getenv('USE_MOCK_DATA', 'False').lower() == 'true',
    'mock_sentiment_score': 0.15,
    'mock_message_content': '這是測試用的市場分析內容。系統正在正常運行中。',

    # 開發工具
    'enable_swagger': True,
    'enable_redoc': True,
    'enable_debug_toolbar': False
}

# ================================
# 環境特定配置 Environment-specific Configuration
# ================================
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

if ENVIRONMENT == 'production':
    # 生產環境設定
    SERVER_CONFIG['debug'] = False
    SERVER_CONFIG['reload'] = False
    SERVER_CONFIG['workers'] = 4
    LOGGING_CONFIG['level'] = 'WARNING'
    SECURITY_CONFIG['enable_rate_limit'] = True
    DEVELOPMENT_CONFIG['debug_mode'] = False
    DEVELOPMENT_CONFIG['verbose_logging'] = False

elif ENVIRONMENT == 'staging':
    # 測試環境設定
    SERVER_CONFIG['debug'] = True
    SERVER_CONFIG['reload'] = False
    LOGGING_CONFIG['level'] = 'INFO'
    SECURITY_CONFIG['enable_rate_limit'] = True

elif ENVIRONMENT == 'development':
    # 開發環境設定
    SERVER_CONFIG['debug'] = True
    SERVER_CONFIG['reload'] = True
    LOGGING_CONFIG['level'] = 'DEBUG'
    SECURITY_CONFIG['enable_rate_limit'] = False
    DEVELOPMENT_CONFIG['verbose_logging'] = True

# ================================
# 功能開關 Feature Flags
# ================================
FEATURE_FLAGS = {
    # 核心功能
    'enable_n8n_integration': True,
    'enable_webhook_forwarding': True,
    'enable_sentiment_analysis': True,

    # 進階功能
    'enable_batch_processing': False,
    'enable_data_analytics': True,
    'enable_report_scheduling': False,
    'enable_multi_language': False,

    # 實驗性功能
    'enable_ai_summary': False,
    'enable_predictive_analysis': False,
    'enable_real_time_updates': True,
    'enable_export_features': False
}

# ================================
# 整合配置 Integration Configuration
# ================================
INTEGRATION_CONFIG = {
    # N8N 整合
    'n8n': {
        'webhook_endpoint': '/api/n8n-data',
        'expected_data_format': 'json',
        'validate_payload': True,
        'max_payload_size': '10MB'
    },

    # 第三方服務
    'external_apis': {
        'market_data_api': {
            'enabled': False,
            'url': os.getenv('MARKET_DATA_API_URL', ''),
            'api_key': os.getenv('MARKET_DATA_API_KEY', ''),
            'timeout': 30
        },
        'notification_service': {
            'enabled': False,
            'url': os.getenv('NOTIFICATION_SERVICE_URL', ''),
            'api_key': os.getenv('NOTIFICATION_SERVICE_API_KEY', '')
        }
    },

    # 資料庫整合（未來擴展）
    'database': {
        'enabled': False,
        'type': os.getenv('DB_TYPE', 'sqlite'),
        'url': os.getenv('DATABASE_URL', 'sqlite:///market_analysis.db'),
        'pool_size': 10,
        'max_overflow': 20
    }
}

# ================================
# UI 配置 User Interface Configuration
# ================================
UI_CONFIG = {
    # 主題設定
    'theme': {
        'default_theme': 'dark',
        'primary_color': '#2563eb',
        'secondary_color': '#f59e0b',
        'success_color': '#10b981',
        'error_color': '#ef4444',
        'warning_color': '#f59e0b'
    },

    # 佈局設定
    'layout': {
        'sidebar_enabled': False,
        'header_fixed': True,
        'footer_enabled': True,
        'breadcrumb_enabled': False
    },

    # 動畫設定
    'animations': {
        'enable_transitions': True,
        'transition_duration': '0.3s',
        'enable_loading_animations': True,
        'enable_hover_effects': True
    },

    # 響應式設定
    'responsive': {
        'mobile_breakpoint': '768px',
        'tablet_breakpoint': '1024px',
        'desktop_breakpoint': '1280px'
    }
}

# ================================
# 快取配置 Cache Configuration
# ================================
CACHE_CONFIG = {
    # 記憶體快取
    'enable_memory_cache': True,
    'memory_cache_size': 100,  # 快取項目數
    'memory_cache_ttl': 300,  # 生存時間（秒）

    # Redis 快取（未來擴展）
    'enable_redis_cache': False,
    'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
    'redis_ttl': 3600,

    # 瀏覽器快取
    'browser_cache_ttl': 300,  # 靜態資源快取時間
    'api_cache_ttl': 60  # API 回應快取時間
}

# ================================
# 備份配置 Backup Configuration
# ================================
BACKUP_CONFIG = {
    # 資料備份
    'enable_auto_backup': False,
    'backup_interval': 'daily',  # daily, weekly, monthly
    'backup_retention': 30,  # 保留天數
    'backup_path': os.getenv('BACKUP_PATH', './backups'),

    # 備份內容
    'backup_data': True,
    'backup_config': True,
    'backup_logs': False,

    # 遠端備份
    'enable_remote_backup': False,
    'remote_backup_url': os.getenv('REMOTE_BACKUP_URL', ''),
    'remote_backup_auth': os.getenv('REMOTE_BACKUP_AUTH', '')
}

# ================================
# 效能配置 Performance Configuration
# ================================
PERFORMANCE_CONFIG = {
    # 並發設定
    'max_concurrent_requests': 100,
    'request_timeout': 30,
    'connection_pool_size': 20,

    # 資源限制
    'max_memory_usage': '512MB',
    'max_cpu_usage': '80%',
    'max_disk_usage': '1GB',

    # 最佳化選項
    'enable_gzip_compression': True,
    'enable_static_file_caching': True,
    'enable_database_pooling': False,
    'enable_lazy_loading': True
}

# ================================
# 通知配置 Notification Configuration
# ================================
NOTIFICATION_CONFIG = {
    # 系統通知
    'enable_system_notifications': True,
    'notification_channels': ['console', 'log'],  # console, log, email, webhook

    # 電子郵件通知（管理員）
    'admin_email_notifications': {
        'enabled': False,
        'smtp_server': os.getenv('SMTP_SERVER', ''),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'smtp_username': os.getenv('SMTP_USERNAME', ''),
        'smtp_password': os.getenv('SMTP_PASSWORD', ''),
        'from_email': os.getenv('ADMIN_FROM_EMAIL', ''),
        'to_emails': os.getenv('ADMIN_TO_EMAILS', '').split(',')
    },

    # Webhook 通知
    'webhook_notifications': {
        'enabled': False,
        'success_webhook': os.getenv('SUCCESS_NOTIFICATION_WEBHOOK', ''),
        'error_webhook': os.getenv('ERROR_NOTIFICATION_WEBHOOK', ''),
        'system_webhook': os.getenv('SYSTEM_NOTIFICATION_WEBHOOK', '')
    }
}


# ================================
# 驗證和確認 Validation and Verification
# ================================
def validate_config():
    """驗證配置設定的有效性"""
    errors = []
    warnings = []

    # 檢查必要的配置
    if not WEBHOOK_CONFIG['send_url']:
        errors.append("WEBHOOK_CONFIG['send_url'] 不能為空")

    if SERVER_CONFIG['port'] < 1 or SERVER_CONFIG['port'] > 65535:
        errors.append("SERVER_CONFIG['port'] 必須在 1-65535 範圍內")

    # 檢查環境變數
    required_env_vars = []
    missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_env_vars:
        warnings.extend([f"環境變數 {var} 未設定" for var in missing_env_vars])

    # 檢查檔案路徑
    log_dir = os.path.dirname(LOGGING_CONFIG['file_path'])
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
            warnings.append(f"已建立日誌目錄: {log_dir}")
        except Exception as e:
            errors.append(f"無法建立日誌目錄 {log_dir}: {str(e)}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def get_config_summary():
    """取得配置摘要資訊"""
    return {
        'environment': ENVIRONMENT,
        'system_name': SYSTEM_INFO['name'],
        'system_version': SYSTEM_INFO['version'],
        'server_host': SERVER_CONFIG['host'],
        'server_port': SERVER_CONFIG['port'],
        'debug_mode': SERVER_CONFIG['debug'],
        'webhook_url': WEBHOOK_CONFIG['send_url'],
        'log_level': LOGGING_CONFIG['level'],
        'features_enabled': sum(1 for v in FEATURE_FLAGS.values() if v),
        'total_features': len(FEATURE_FLAGS)
    }


# ================================
# 配置匯出 Configuration Export
# ================================
def export_config_for_frontend():
    """匯出給前端使用的配置"""
    return {
        'system_info': SYSTEM_INFO,
        'ui_config': UI_CONFIG,
        'feature_flags': FEATURE_FLAGS,
        'sentiment_config': {
            'labels': SENTIMENT_CONFIG['labels'],
            'colors': SENTIMENT_CONFIG['colors'],
            'emojis': SENTIMENT_CONFIG['emojis']
        }
    }


# ================================
# 初始化檢查 Initialization Check
# ================================
if __name__ == "__main__":
    print("🔧 市場分析系統配置檔案")
    print("=" * 50)

    # 執行配置驗證
    validation_result = validate_config()

    if validation_result['valid']:
        print("✅ 配置驗證通過")
    else:
        print("❌ 配置驗證失敗")
        for error in validation_result['errors']:
            print(f"   錯誤: {error}")

    for warning in validation_result['warnings']:
        print(f"⚠️  警告: {warning}")

    print("\n📊 配置摘要:")
    summary = get_config_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print(f"\n🌐 系統將在 http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']} 啟動")
    print(f"📡 Webhook 目標: {WEBHOOK_CONFIG['send_url']}")
    print(f"🔧 環境模式: {ENVIRONMENT}")

    if SERVER_CONFIG['debug']:
        print("⚠️  除錯模式已啟用")

    print("\n" + "=" * 50)