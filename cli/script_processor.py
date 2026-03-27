"""Post-process Playwright codegen scripts to support shared browser session state."""

import re


def inject_storage_state(script_content: str) -> str:
    """Inject storage state load/save into a Playwright codegen script.

    Transforms:
        context = browser.new_context()
    Into:
        import os as _qc_os
        _qc_state = _qc_os.environ.get("QACLAN_STORAGE_STATE")
        context = browser.new_context(
            storage_state=_qc_state if _qc_state and _qc_os.path.exists(_qc_state) else None
        )

    And inserts before context.close():
        if _qc_state:
            context.storage_state(path=_qc_state)
    """
    # Add os import at the top (use prefixed name to avoid conflicts)
    if "import os as _qc_os" not in script_content:
        script_content = "import os as _qc_os\n" + script_content

    # Inject state variable after the import block
    state_var = '_qc_state = _qc_os.environ.get("QACLAN_STORAGE_STATE")\n'
    if "_qc_state" not in script_content:
        # Insert after the last import line
        lines = script_content.split("\n")
        last_import = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                last_import = i
        lines.insert(last_import + 1, state_var.rstrip())
        script_content = "\n".join(lines)

    # Replace browser.new_context() with storage_state-aware version
    # Handle: browser.new_context() and browser.new_context(**kwargs)
    script_content = re.sub(
        r'([ \t]*)(context\s*=\s*browser\.new_context)\(\)',
        r'\1\2(\n\1    storage_state=_qc_state if _qc_state and _qc_os.path.exists(_qc_state) else None\n\1)',
        script_content,
    )

    # If new_context has existing args, add storage_state as first arg
    script_content = re.sub(
        r'([ \t]*)(context\s*=\s*browser\.new_context)\((?!\s*\n\s*storage_state)(.*?)\)',
        r'\1\2(\n\1    storage_state=_qc_state if _qc_state and _qc_os.path.exists(_qc_state) else None,\n\1    \3\n\1)',
        script_content,
    )

    # Insert storage state save before context.close()
    if "context.storage_state(path=_qc_state)" not in script_content:
        def _insert_save(m):
            indent = m.group(1)
            save = f"{indent}if _qc_state:\n{indent}    context.storage_state(path=_qc_state)\n"
            return f"{save}{indent}{m.group(2)}"

        script_content = re.sub(
            r'([ \t]*)(context\.close\(\))',
            _insert_save,
            script_content,
            count=1,
        )

    return script_content
