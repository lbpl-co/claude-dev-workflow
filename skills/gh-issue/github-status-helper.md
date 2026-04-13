# GitHub Projects Status Helper

Use these `gh` CLI commands to read and update the **Status** field on a GitHub Projects item.

> **Note:** Status is a Projects board field — NOT a label. Never use `gh issue edit --label` for workflow state.

## Statuses

| Status | Meaning |
|--------|---------|
| `Todo` | Not started |
| `In Analysis` | Analysis in progress or complete, awaiting development |
| `In Progress` | Development underway |
| `In Review` | PR created, awaiting review |
| `Done` | Merged / complete |

## 1. Find the project number

```bash
gh project list --owner <org-or-user>
# Returns: NUMBER  TITLE  URL
```

## 2. Find the item ID for a specific issue

```bash
gh project item-list <project-number> --owner <org-or-user> --format json \
  | jq '.items[] | select(.content.number == <issue-number>) | {id: .id, title: .content.title}'
```

## 3. Read current status

```bash
gh project item-list <project-number> --owner <org-or-user> --format json \
  | jq '.items[] | select(.content.number == <issue-number>) | {id: .id, status: .status, title: .content.title}'
```

## 4. List Status field ID and all option IDs

```bash
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "Status") | {fieldId: .id, options: .options}'
# Returns field ID and option objects: {id, name} for each status value
```

## 5. Get project node ID (needed for item-edit)

```bash
gh project list --owner <org-or-user> --format json \
  | jq '.projects[] | select(.number == <project-number>) | .id'
```

## 6. Update status

```bash
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <status-field-id> \
  --single-select-option-id <option-id>
```

## 7. Update a single-select field (e.g. Size, Task Type)

```bash
# List field ID and all option IDs:
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "<FieldName>") | {fieldId: .id, options: .options}'

# Update:
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <field-id> \
  --single-select-option-id <option-id>
```

## 8. Update a number field (e.g. Estimate)

```bash
# Find field ID:
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "Estimate") | .id'

# Update:
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <field-id> \
  --number <value>
```

## 9. Update a date field (e.g. End date)

```bash
# Find field ID:
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "End date") | .id'

# Update (ISO 8601 format):
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <field-id> \
  --date "YYYY-MM-DD"
```

## 10. Update an iteration field (e.g. Iteration)

```bash
# List field ID and all iteration IDs:
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "Iteration") | {fieldId: .id, iterations: .configuration.iterations}'

# Update:
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <field-id> \
  --iteration-id <iteration-id>
```

## 11. Update branch_link (text field)

```bash
# First find the field ID for branch_link:
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "branch_link") | .id'

# Then update:
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <branch-link-field-id> \
  --text "<branch-name>"
```

## Status transitions

| Moment | Set status to |
|--------|--------------|
| Analysis posted | `In Analysis` |
| Starting implementation | `In Progress` |
| PR created, awaiting review | `In Review` |
| PR merged | `Done` |
