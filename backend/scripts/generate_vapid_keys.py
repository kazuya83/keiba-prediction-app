"""VAPID 鍵の生成を行うユーティリティスクリプト。"""

from __future__ import annotations

import sys
from textwrap import dedent


def main() -> None:
    try:
        from py_vapid import Vapid
    except ImportError:  # pragma: no cover - 実行環境依存
        sys.stderr.write(
            "pywebpush / py-vapid がインストールされていません。`poetry add pywebpush` 後に再実行してください。\n",
        )
        raise SystemExit(1) from None

    vapid = Vapid()
    private_key, public_key = vapid.create_keys()

    message = dedent(
        f"""
        === Generated VAPID Keys ===

        NOTIFICATION_VAPID_PUBLIC_KEY={public_key}
        NOTIFICATION_VAPID_PRIVATE_KEY={private_key}
        NOTIFICATION_VAPID_SUBJECT=mailto:notify@example.com

        1. 公開鍵と秘密鍵は Secrets Manager や .env など安全な場所に保存してください。
        2. `NOTIFICATION_VAPID_SUBJECT` は通知受信者が連絡を取れるアドレスに変更してください。
        3. 環境変数を設定した後、FastAPI アプリケーションを再起動すると Push 通知が利用可能になります。
        """
    ).strip()
    print(message)


if __name__ == "__main__":
    main()


