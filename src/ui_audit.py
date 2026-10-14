"""Read-only widget text checks used by source and frozen acceptance tests."""
import re

FORBIDDEN = re.compile(r'\b(Whisper|CUDA|float16|CTranslate2|WASAPI|loopback|Ready|Loading|Translation|English|Microphone|Auto|Fast|Balanced|Accurate|Pending|Start|Stop|snapshot)\b')

def inspect_labels(root):
    violations = []
    count = 0
    def visit(widget):
        nonlocal count
        for option in ('text', 'values'):
            if option in widget.keys():
                value = str(widget.cget(option))
                count += bool(value)
                if FORBIDDEN.search(value):
                    violations.append(value)
        for child in widget.winfo_children(): visit(child)
    visit(root)
    return {'checked_labels': count, 'violations': violations, 'passed': not violations}
