import requests
import json
from datetime import datetime
import sys
import time

# 設定配置
CONFIG = {
    "webhook_url": "https://beloved-swine-sensibly.ngrok-free.app/webhook-test/Webhook - Preview",
    "timeout": 30,
    "default_subject": "市場分析報告",
    "market_data": [
        {
            "average_sentiment_score": 0.1,
            "message": {
                "content": "今日市場概述：黃金價格在全球貿易緊張情勢與美國通脹數據影響下出現小幅反彈。印度金價於兩日回調後反彈至每10克97,389盧比，顯示出投資者對避險資產的需求。美國股市則因市場預期美國聯邦儲備將延後降息而面臨波動，導致美元指數上漲，這可能進一步影響黃金的走勢。投資者應關注即將發布的美國通脹數據，以判斷黃金市場的下一步動向。"
            }
        }
    ]
}


class EmailSender:
    def __init__(self):
        self.webhook_url = CONFIG["webhook_url"]
        self.timeout = CONFIG["timeout"]
        self.market_data = CONFIG["market_data"]

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "email-sender-client",
            "Accept": "application/json"
        })

    def send_email(self, email, subject=None, custom_message=None):
        """發送郵件 (使用 GET 方式)"""
        if not self._validate_email(email):
            print("❌ 無效的郵件地址格式")
            return False

        if subject is None:
            subject = CONFIG["default_subject"]

        # 構建郵件內容
        email_content = self._build_email_content(custom_message)

        # 準備 GET 請求參數
        params = {
            "to": email,
            "subject": subject,
            "content": email_content,
            "data": json.dumps(self.market_data, ensure_ascii=False),
            "timestamp": datetime.now().isoformat(),
            "sentiment_score": self.market_data[0]["average_sentiment_score"]
        }

        print(f"📧 發送郵件到: {email}")
        print(f"📋 主題: {subject}")
        print(f"📊 情緒評分: {self.market_data[0]['average_sentiment_score']}")
        print(f"🔗 Webhook URL: {self.webhook_url}")
        print("-" * 50)

        try:
            response = self.session.get(
                self.webhook_url,
                params=params,
                timeout=self.timeout
            )

            return self._handle_response(response)

        except requests.exceptions.Timeout:
            print("❌ 請求超時")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ 連接錯誤，請檢查 ngrok 服務是否運行")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 請求錯誤: {e}")
            return False
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")
            return False

    def _validate_email(self, email):
        """驗證郵件地址格式"""
        return "@" in email and "." in email.split("@")[-1]

    def _build_email_content(self, custom_message=None):
        """構建郵件內容"""
        lines = []

        if custom_message:
            lines.append(custom_message)
            lines.append("")

        lines.append("=== 市場分析報告 ===")
        lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        data = self.market_data[0]

        # 情緒評分
        score = data["average_sentiment_score"]
        sentiment_text = self._get_sentiment_text(score)
        lines.append(f"市場情緒評分: {score} ({sentiment_text})")
        lines.append("")

        # 市場分析內容
        lines.append("市場分析:")
        lines.append(data["message"]["content"])
        lines.append("")
        lines.append("--- 報告結束 ---")

        return "\n".join(lines)

    def _get_sentiment_text(self, score):
        """根據評分返回情緒文字"""
        if score >= 0.5:
            return "正面"
        elif score >= 0.0:
            return "中性偏正"
        elif score >= -0.5:
            return "中性偏負"
        else:
            return "負面"

    def _handle_response(self, response):
        """處理回應"""
        print(f"回應狀態碼: {response.status_code}")

        if response.content:
            try:
                response_json = response.json()
                print(f"回應內容: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"回應內容: {response.text}")
        else:
            print("回應內容: 空")

        success = 200 <= response.status_code < 300

        if success:
            print("✅ 郵件發送成功！")
        else:
            print(f"❌ 郵件發送失敗，狀態碼: {response.status_code}")

        return success

    def send_single_email(self):
        """發送單一郵件"""
        print("\n=== 發送市場分析郵件 ===")

        email = input("請輸入收件人郵件地址: ").strip()
        if not email:
            print("❌ 未輸入郵件地址")
            return False

        subject = input(f"請輸入郵件主題 (Enter 使用預設: {CONFIG['default_subject']}): ").strip()
        if not subject:
            subject = CONFIG["default_subject"]

        custom_message = input("請輸入自定義開頭訊息 (Enter 跳過): ").strip()
        if not custom_message:
            custom_message = None

        return self.send_email(email, subject, custom_message)

    def send_multiple_emails(self):
        """發送多個郵件"""
        print("\n=== 批量發送市場分析郵件 ===")

        print("請輸入多個郵件地址 (每行一個，空行結束):")
        emails = []
        while True:
            try:
                email = input().strip()
                if not email:
                    break
                if self._validate_email(email):
                    emails.append(email)
                else:
                    print(f"❌ 跳過無效郵件: {email}")
            except (EOFError, KeyboardInterrupt):
                break

        if not emails:
            print("❌ 未輸入任何有效郵件地址")
            return False

        subject = input(f"請輸入郵件主題 (Enter 使用預設: {CONFIG['default_subject']}): ").strip()
        if not subject:
            subject = CONFIG["default_subject"]

        print(f"\n準備發送到 {len(emails)} 個郵件地址...")

        success_count = 0
        for i, email in enumerate(emails, 1):
            print(f"\n--- 發送 {i}/{len(emails)} ---")

            if self.send_email(email, subject):
                success_count += 1

            if i < len(emails):
                print("等待 2 秒...")
                time.sleep(2)

        print(f"\n=== 發送結果 ===")
        print(f"成功: {success_count}/{len(emails)}")
        print(f"成功率: {(success_count / len(emails)) * 100:.1f}%")

        return success_count > 0


def show_menu():
    """顯示選單"""
    print("\n" + "=" * 50)
    print("📧 市場分析郵件發送工具")
    print("=" * 50)
    print("1. 發送單一郵件")
    print("2. 批量發送郵件")
    print("3. 顯示設定")
    print("4. 預覽郵件內容")
    print("5. 退出")


def show_config():
    """顯示設定資訊"""
    print("\n=== 目前設定 ===")
    print(f"Webhook URL: {CONFIG['webhook_url']}")
    print(f"超時時間: {CONFIG['timeout']} 秒")
    print(f"預設主題: {CONFIG['default_subject']}")
    print(f"當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n=== 市場資料 ===")
    data = CONFIG['market_data'][0]
    print(f"情緒評分: {data['average_sentiment_score']}")
    print(f"內容長度: {len(data['message']['content'])} 字元")
    print(f"內容預覽: {data['message']['content'][:100]}...")


def preview_email_content():
    """預覽郵件內容"""
    print("\n=== 郵件內容預覽 ===")

    sender = EmailSender()
    content = sender._build_email_content("這是一個範例開頭訊息")

    print("以下是將要發送的郵件內容:")
    print("-" * 50)
    print(content)
    print("-" * 50)


def main():
    """主程式"""
    print("🚀 啟動市場分析郵件發送工具")

    # 檢查 requests 套件
    try:
        import requests
        print("✅ requests 套件已安裝")
    except ImportError:
        print("❌ 需要安裝 requests 套件")
        print("請執行: pip install requests")
        sys.exit(1)

    sender = EmailSender()

    while True:
        show_menu()

        try:
            choice = input("\n請選擇 (1-5): ").strip()

            if choice == "1":
                sender.send_single_email()
            elif choice == "2":
                sender.send_multiple_emails()
            elif choice == "3":
                show_config()
            elif choice == "4":
                preview_email_content()
            elif choice == "5":
                print("👋 再見！")
                break
            else:
                print("❌ 無效選項，請選擇 1-5")

        except KeyboardInterrupt:
            print("\n\n程式中斷")
            break
        except Exception as e:
            print(f"❌ 程式錯誤: {e}")

        input("\n按 Enter 繼續...")


if __name__ == "__main__":
    main()