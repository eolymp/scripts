# Participant Importer

Adds space members as participants to a contest from a CSV file containing display names.

## Usage

```
EOLYMP_TOKEN=<token> python participant-importer.py [options] <space_key> <contest_id> <input>
```

### Arguments

| Argument | Description |
|---|---|
| `space_key` | Space key |
| `contest_id` | Contest ID |
| `input` | Path to CSV file |

### Options

| Option | Description |
|---|---|
| `--unofficial` | Add participants as unofficial |
| `--inactive` | Add participants as inactive |

## CSV Format

The CSV file must have a `display_name` column. Values containing commas must be quoted.

```csv
display_name
"Team Alpha: Smith, Jones, Brown"
"Team Beta: Doe, Johnson"
SingleMember
```
