import math
from datetime import datetime, timezone


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def build_pagination(page, limit, total):
    page = max(int(page), 1)
    limit = max(int(limit), 1)
    total = max(int(total), 0)
    total_pages = math.ceil(total / limit) if total else 0
    offset = (page - 1) * limit

    pagination = {
        "page": page,
        "limit": limit,
        "offset": offset,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total_pages > 0,
    }

    if pagination["has_next"]:
        pagination["next_page"] = page + 1
    if pagination["has_previous"]:
        pagination["previous_page"] = page - 1

    return pagination


def remove_nulls(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            cleaned_item = remove_nulls(item)
            if cleaned_item is not None:
                cleaned[key] = cleaned_item
        return cleaned or None
    if isinstance(value, list):
        cleaned_list = [remove_nulls(item) for item in value]
        return [item for item in cleaned_list if item is not None]
    return value


def success_response(message, data, meta=None, status_code=200):
    payload = remove_nulls(
        {
            "success": True,
            "message": message,
            "data": data,
            "meta": {
                "timestamp": utc_now_iso(),
                **(meta or {}),
            },
        }
    )
    return payload, status_code


def error_response(message, code, details=None, status_code=400):
    payload = {
        "success": False,
        "message": message,
        "error": {
            "code": code,
            "details": details or message,
        },
        "meta": {
            "timestamp": utc_now_iso(),
        },
    }
    return payload, status_code
