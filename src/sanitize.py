import re


def sanitize_title(title: str | None) -> str:
    """タイトルをファイル名として使用できる形式に sanitize する関数

    Args:
        title (str | None): 元のタイトル

    Returns:
        str: 置換後のファイル名
    """
    # ファイル名に使用できない文字を置換
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", title or "").strip(" .")
    return sanitized
