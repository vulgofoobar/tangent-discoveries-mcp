import re
import os
from datetime import datetime
from pathlib import Path
from pydantic import Field
from mcp.server.fastmcp import FastMCP

env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

mcp = FastMCP("ObsidianMCP", log_level="ERROR")

if "OBSIDIAN_ROUGH_NOTES" in os.environ:
    rough_notes_path = os.environ["OBSIDIAN_ROUGH_NOTES"]
    if rough_notes_path.startswith("~"):
        rough_notes_path = rough_notes_path.replace("~", str(Path.home()), 1)
    ROUGH_NOTES = Path(rough_notes_path)
else:
    ROUGH_NOTES = Path("rough-notes")

@mcp.resource(
    "obsidian://rough-notes",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    if ROUGH_NOTES.exists():
        return [f.name for f in ROUGH_NOTES.glob("*.md")]
    return []

@mcp.resource(
    "obsidian://rough-notes/{filename}",
    mime_type="text/markdown"
)
def get_rough_note(filename: str) -> str:
    filepath = ROUGH_NOTES / filename
    if not filepath.exists():
        raise ValueError(f"File not found: {filename}")
    return filepath.read_text()

@mcp.tool(
    name="create_tangent_discoveries",
    description="Extract 'see' discoveries from a note file, create separate files for each and update references."
)
def create_tangent_discoveries(
    filename: str = Field(description="The .md filename from rough notes to process")
):
    filepath = ROUGH_NOTES / filename

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
        new_filepath = ROUGH_NOTES / new_filename

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
