import json
from datetime import datetime

with open('violations.json') as f:
    violations_data = json.load(f)

# Debug: Print the structure to understand the format
print("JSON structure:")
print(json.dumps(violations_data, indent=2)[:500] + "..." if len(str(violations_data)) > 500 else json.dumps(violations_data, indent=2))

# Check for OPA errors first
if 'errors' in violations_data and violations_data['errors']:
    print("❌ OPA encountered errors:")
    for error in violations_data['errors']:
        print(f"   • {error.get('message', 'Unknown error')}")

    # Generate error report
    md = f"# Violations Summary\n_Scanned: {datetime.utcnow().isoformat()}Z_\n\n"
    md += "## ❌ Scan Failed\n\n"
    md += "OPA encountered the following errors:\n\n"
    for error in violations_data['errors']:
        md += f"- {error.get('message', 'Unknown error')}\n"

    with open('docs/violations_summary.md', 'w') as f:
        f.write(md)

    print("❌ Scan failed. Error report written to docs/violations_summary.md")
    exit(1)

# Try to extract violations with error handling
violations = None

# Common OPA result structures to try
possible_paths = [
    # Standard OPA format
    lambda data: data['result'][0]['expressions'][0]['value'],
    # Alternative OPA formats
    lambda data: data['result'],
    lambda data: data['results'][0]['expressions'][0]['value'],
    lambda data: data['results'],
    # Direct format
    lambda data: data['violations'],
]

for i, path_func in enumerate(possible_paths):
    try:
        violations = path_func(violations_data)
        print(f"✅ Successfully extracted violations using path #{i+1}")
        break
    except (KeyError, IndexError, TypeError) as e:
        print(f"❌ Path #{i+1} failed: {e}")
        continue

if violations is None:
    print("❌ Could not extract violations from JSON. Please check the file structure.")
    exit(1)

# Generate markdown
md = f"# Violations Summary\n_Scanned: {datetime.utcnow().isoformat()}Z_\n\n"

if violations:
    # Handle different violation formats
    if isinstance(violations, dict):
        for rule, msgs in violations.items():
            md += f"## {rule}\n"
            if isinstance(msgs, list):
                for msg in msgs:
                    md += f"- {msg}\n"
            else:
                md += f"- {msgs}\n"
    elif isinstance(violations, list):
        md += "## Violations\n"
        for violation in violations:
            md += f"- {violation}\n"
    else:
        md += f"## Violations\n- {violations}\n"
else:
    md += "✅ No violations found!\n"

with open('docs/violations_summary.md', 'w') as f:
    f.write(md)

print("✅ docs/violations_summary.md created!")
