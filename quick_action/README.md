# Quick Action Template

This folder is a placeholder for the Automator **Quick Action** bundle. Create a Quick Action in Automator that calls the project CLI, then place the `.workflow` bundle here so the install script can copy it to `~/Library/Services`.

## Create the Quick Action

1) Open **Automator** → **New Document** → choose **Quick Action**.  
2) Configure:
   - *Workflow receives current*: **files or folders** in **Finder**.
   - *Output replaces selected text*: leave unchecked.
3) Add the **Run Shell Script** action. Set:
   - *Shell*: `/bin/bash`
   - *Pass input*: `as arguments`
   - *Script* (update `APP_ROOT` to your clone):
     ```bash
     APP_ROOT="${HOME}/Development/cyapow/rsync/rsync-quick-action"
     python3 "${APP_ROOT}/src/cli.py" "$@"
     ```
4) Save as `Rsync Quick Action.workflow`.
5) Drop the saved `.workflow` bundle into `quick_action/` and run `scripts/install_quick_action.sh`.

If you move the repo, edit the `APP_ROOT` line inside the Automator Run Shell Script.
