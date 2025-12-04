# backend/app/core/security.py
import os
from cryptography.fernet import Fernet

# 建議在 .env 設定 ENCRYPTION_KEY，若無則每次重啟會隨機生成 (導致舊資料無法解密)
# 生成方式: Fernet.generate_key().decode()
_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(_key)


def encrypt_value(value: str) -> str:
    if not value:
        return None
    return cipher_suite.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return None
    try:
        return cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # 解密失敗 (可能是 Key 換了或是資料損毀)
        return None
