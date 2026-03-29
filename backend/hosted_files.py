"""
Hosted AI files module for AgentCheck.

Generates and manages hosted ai.txt, llms.txt, and robots_txt_additions
files that users can link to from their domains.
"""

import secrets
import uuid

from fix_generator import generate_fixes
from db import (
    save_hosted_file,
    get_hosted_files,
    update_hosted_file_content,
)

# File types we extract and host from generate_fixes output
HOSTED_FILE_TYPES = {
    "ai.txt": "ai.txt",
    "llms.txt": "llms.txt",
    "robots_txt_additions.txt": "robots_txt_additions.txt",
}


async def activate_hosted_files(user_id: str, domain: str, scan_id: str) -> list[dict]:
    """
    Generate fix files for a scan and save the hostable ones to the DB.

    Args:
        user_id: The authenticated user's ID.
        domain: The domain that was scanned.
        scan_id: The completed scan ID to generate fixes from.

    Returns:
        List of created hosted file records.
    """
    result = await generate_fixes(scan_id)
    files_by_name = {f["name"]: f["content"] for f in result["files"]}

    created = []
    for file_name, file_type in HOSTED_FILE_TYPES.items():
        content = files_by_name.get(file_name)
        if not content:
            continue

        file_id = str(uuid.uuid4())
        public_token = secrets.token_urlsafe(8)

        await save_hosted_file(
            file_id=file_id,
            user_id=user_id,
            domain=domain,
            file_type=file_type,
            content=content,
            public_token=public_token,
        )

        created.append({
            "id": file_id,
            "domain": domain,
            "file_type": file_type,
            "public_token": public_token,
        })

    return created


async def refresh_hosted_files(user_id: str, domain: str, scan_id: str) -> list[dict]:
    """
    Regenerate hosted file contents after a re-scan. Updates existing records.

    Args:
        user_id: The authenticated user's ID.
        domain: The domain that was scanned.
        scan_id: The new completed scan ID.

    Returns:
        List of updated hosted file records.
    """
    result = await generate_fixes(scan_id)
    files_by_name = {f["name"]: f["content"] for f in result["files"]}

    existing = await get_hosted_files(user_id, domain)
    existing_by_type = {f["file_type"]: f for f in existing}

    updated = []
    for file_name, file_type in HOSTED_FILE_TYPES.items():
        content = files_by_name.get(file_name)
        if not content:
            continue

        record = existing_by_type.get(file_type)
        if record:
            await update_hosted_file_content(record["id"], content)
            updated.append({
                "id": record["id"],
                "domain": domain,
                "file_type": file_type,
                "public_token": record["public_token"],
            })
        else:
            # File type didn't exist before — create it
            file_id = str(uuid.uuid4())
            public_token = secrets.token_urlsafe(8)
            await save_hosted_file(
                file_id=file_id,
                user_id=user_id,
                domain=domain,
                file_type=file_type,
                content=content,
                public_token=public_token,
            )
            updated.append({
                "id": file_id,
                "domain": domain,
                "file_type": file_type,
                "public_token": public_token,
            })

    return updated
