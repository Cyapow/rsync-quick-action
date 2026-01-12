# Rsync Quick Action

A macOS Quick Action that integrates rsync functionality into the Finder context menu, allowing users to efficiently synchronize files and folders to mounted drives through a simple right-click interface.

## Project Structure

```
rsync-quick-action/
├── src/                    # Source code
│   ├── gui/               # GUI application components
│   ├── rsync_wrapper/     # Rsync command wrapper
│   └── drive_detection/   # Drive detection utilities
├── quick_action/          # macOS Quick Action workflow
├── scripts/              # Install/uninstall helpers
├── tests/                 # Test suite
├── config/               # Configuration files
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## Development Setup

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the GUI directly (bypassing Finder) with sample sources:
   ```bash
   python src/cli.py /path/to/source1 /path/to/source2
   ```

## Requirements

- macOS 10.14 or later
- Python 3.8 or later
- rsync (included with macOS)

## Components

- **Quick Action**: macOS Automator service for Finder integration
- **GUI Application**: User interface for drive selection and progress monitoring
- **Rsync Wrapper**: Command-line utility for executing synchronization operations
- **Drive Detection**: System integration for mounted drive enumeration

## Create the macOS Quick Action

1. Open **Automator** → **New Document** → select **Quick Action**.
2. At the top, set:
   - *Workflow receives*: `files or folders`
   - *in*: `Finder`
   - Leave "Output replaces selected text" unchecked.
3. Add a **Run Shell Script** action with:
   - Shell: `/bin/bash`
   - Pass input: `as arguments`
   - Script (update `APP_ROOT` to your clone):
     ```bash
     APP_ROOT="${HOME}/Development/cyapow/rsync/rsync-quick-action"
     python3 "${APP_ROOT}/src/cli.py" "$@"
     ```
4. Save as `Rsync Quick Action.workflow`.
5. Place the saved bundle in `quick_action/` and run:
   ```bash
   scripts/install_quick_action.sh
   ```
6. If you move the repo, edit the path in the Automator action and reinstall. To remove the Quick Action:
   ```bash
   scripts/uninstall_quick_action.sh
   ```

## Usage

Finder:
- Select files/folders → right-click → `Rsync Quick Action` → GUI opens → choose destination drive/folder and options → Start Sync.

Terminal (for testing):
- `python src/cli.py /path/to/src1 /path/to/src2`

## Testing

Run the full test suite (property-based tests use Hypothesis):
```bash
pytest
```
