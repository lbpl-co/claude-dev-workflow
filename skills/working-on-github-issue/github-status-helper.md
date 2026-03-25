# GitHub Projects Status Helper

Use these `gh` CLI commands to read and update the **Status** field on a GitHub Projects item.

> **Note:** Status is a Projects board field — NOT a label. Never use `gh issue edit --label` for workflow state.

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

## 3. List Status field ID and all option IDs

```bash
gh project field-list <project-number> --owner <org-or-user> --format json \
  | jq '.fields[] | select(.name == "Status") | {fieldId: .id, options: .options}'
# Returns field ID and option objects: {id, name} for each status value
```

## 4. Update status

```bash
gh project item-edit \
  --project-id <project-node-id> \
  --id <item-node-id> \
  --field-id <status-field-id> \
  --single-select-option-id <option-id>
```

## 5. Get project node ID (needed for item-edit)

```bash
gh project list --owner <org-or-user> --format json \
  | jq '.projects[] | select(.number == <project-number>) | .id'
```

## Common Status Transitions

| Moment | Status to set |
|--------|--------------|
| Starting analysis | `In Develop` |
| Starting implementation | `In Develop` |
| PR created, awaiting review | `In Review` |
| PR merged | `Done` |
