"""OpenAPI仕様をエクスポートするスクリプト。"""

import json
from pathlib import Path

from app.main import app


def export_openapi_spec(output_path: Path) -> None:
    """OpenAPI仕様をJSONファイルにエクスポートする。"""
    openapi_schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    print(f"OpenAPI仕様をエクスポートしました: {output_path}")


if __name__ == "__main__":
    # プロジェクトルートからの相対パス
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "docs" / "api" / "openapi.json"
    export_openapi_spec(output_path)

