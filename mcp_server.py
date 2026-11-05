import re
from datetime import datetime
from pathlib import Path
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ObsidianMCP", log_level="ERROR")

VAULT_ROUGH_NOTES = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault 32/01. rough notes"

@mcp.resource(
    "obsidian://rough-notes",
    mime_type="application/json"
)
def list_rough_notes() -> list[str]:
    if not VAULT_ROUGH_NOTES.exists():
        return []
    return [f.name for f in VAULT_ROUGH_NOTES.glob("*.md")]

@mcp.tool(
    name="create_tangent_discoveries",
    description="Extract 'see' discoveries from a note file, create separate files for each and update references."
)
def create_tangent_discoveries(
    filename: str = Field(description="The .md filename from rough notes to process")
):
    filepath = VAULT_ROUGH_NOTES / filename

    if not filepath.exists():
        raise ValueError(f"File not found: {filename}")

    content = filepath.read_text()

    discovery_pattern = r"^see\s+(.+?)$"
    matches = list(re.finditer(discovery_pattern, content, re.MULTILINE))

    if not matches:
        return {"message": "No discoveries found", "created": 0, "updated": 0}

    created_count = 0
    updated_count = 0
    updated_content = content

    for match in matches:
        discovery_name = match.group(1).strip()
        match_start = match.start()
        discovery_start = match.end()

        next_see = content.find("see ", discovery_start)
        if next_see == -1:
            discovery_section = content[discovery_start:]
            section_end = len(content)
        else:
            discovery_section = content[discovery_start:next_see]
            section_end = next_see

        tag_pattern = r"\[\[([^\]]+)\]\]"
        tags = re.findall(tag_pattern, discovery_section)

        lines = discovery_section.strip().split("\n")
        note_lines = []
        for line in lines:
            if line.strip() and not line.startswith("[["):
                note_lines.append(line)
            elif note_lines and not line.strip():
                break

        new_filename = f"{discovery_name}.md"
        new_filepath = VAULT_ROUGH_NOTES / new_filename

        if new_filepath.exists():
            updated_count += 1
            continue

        today = datetime.now().strftime("%Y-%m-%d %H:%M")
        tag_lines = " ".join(f"[[{tag}]]" for tag in tags) if tags else ""
        notes_content = "\n\n".join(note_lines).strip()

        new_content = f"""{today}

status: #child

tags: {tag_lines}

# {discovery_name}

{notes_content}




# references
"""

        new_filepath.write_text(new_content)
        created_count += 1

        old_section = content[match_start:section_end].rstrip()
        new_ref = f"see [[{discovery_name}]]"
        updated_content = updated_content.replace(old_section, new_ref)

    filepath.write_text(updated_content)

    return {
        "file": filename,
        "discoveries_found": len(matches),
        "files_created": created_count,
        "duplicates_skipped": updated_count
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
