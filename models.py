from pydantic import BaseModel, validator
import re


class EmailRequest(BaseModel):
    """郵件發送請求模型 - 只需要 to 欄位"""
    to: str

    @validator('to')
    def validate_email(cls, v):
        """驗證電子郵件格式"""
        if not v or not v.strip():
            raise ValueError('電子郵件地址不能為空')

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError('請輸入有效的電子郵件地址')

        return v.lower().strip()

    class Config:
        """模型設定"""
        # 提供範例資料
        schema_extra = {
            "example": {
                "to": "user@example.com"
            }
        }