import re
import tempfile
from pathlib import Path
from datetime import datetime

def create_tangent_discoveries(filepath, vault_path):
    """Minimal version without MCP for validation."""
    content = filepath.read_text()

    discovery_pattern = r"^see\s+(.+?)$"
    matches = list(re.finditer(discovery_pattern, content, re.MULTILINE))

    if not matches:
        return {"message": "No discoveries found", "created": 0}

    created_count = 0
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
        new_filepath = vault_path / new_filename

        if new_filepath.exists():
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
        "discoveries_found": len(matches),
        "files_created": created_count
    }


def test():
    """Test discovery extraction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)

        test_content = """see what's the code to create an mcp server w mcp sdk?
[[dev]] [[ai]]
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("DocumentMCP", log_level="ERROR")

see why does mcp matters?
[[ai]] [[protocol]]
open source protocol
connects ai with external systems

"""

        test_file = vault / "notes.md"
        test_file.write_text(test_content)

        result = create_tangent_discoveries(test_file, vault)

        print(f"✓ Found {result['discoveries_found']} discoveries")
        print(f"✓ Created {result['files_created']} files\n")

        created_files = sorted([f.name for f in vault.glob("*.md") if f != test_file])
        for fname in created_files:
            print(f"=== {fname} ===")
            content = (vault / fname).read_text()
            print(content)
            print()

        print("=== notes.md (updated) ===")
        updated = test_file.read_text()
        print(updated)

if __name__ == "__main__":
    test()
