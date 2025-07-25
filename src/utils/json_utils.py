# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
import json
import json_repair

logger = logging.getLogger(__name__)


def repair_json_output(content: str) -> str:
    """
    Repair and normalize JSON output.

    Args:
        content (str): String content that may contain JSON

    Returns:
        str: Repaired JSON string, or original content if not JSON
    """
    content = content.strip()

    try:
        # Try to repair and parse JSON
        repaired_content = json_repair.loads(content)
        if not isinstance(repaired_content, dict) and not isinstance(
            repaired_content, list
        ):
            logger.warning("Repaired content is not a valid JSON object or array.")
            return content
        content = json.dumps(repaired_content, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"JSON repair failed: {e}")

    return content


def safe_json_loads(content: str) -> dict:
    """
    Safely load JSON content with error handling.

    Args:
        content (str): JSON string content

    Returns:
        dict: Parsed JSON object, or empty dict if parsing fails
    """
    if not content:
        return {}

    try:
        # First try standard JSON parsing
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            # Try with json_repair if standard parsing fails
            return json_repair.loads(content)
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}")
            return {}
