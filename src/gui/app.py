from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable, Optional

from configuration import PreferencesStore, UserPreferences
from drive_detection import DriveDetector, validate_destination
from rsync_wrapper import RsyncCommandBuilder, RsyncRunner, SyncOptions


class RsyncQuickActionApp:
    def __init__(
        self,
        sources: Iterable[Path | str],
        detector: Optional[DriveDetector] = None,
        command_builder: Optional[RsyncCommandBuilder] = None,
        runner: Optional[RsyncRunner] = None,
        preferences_store: Optional[PreferencesStore] = None,
    ) -> None:
        self.sources = [Path(src) for src in sources]
        self.detector = detector or DriveDetector()
        self.command_builder = command_builder or RsyncCommandBuilder()
        self.runner = runner or RsyncRunner()
        self.preferences_store = preferences_store or PreferencesStore()
        self.preferences = self.preferences_store.load()

        self.root = tk.Tk()
        self.root.title("Rsync to Drive")
        self.root.geometry("600x430")

        self.drive_list = None
        self.destination_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var = tk.StringVar(value="Waiting to start")
        self.option_vars: dict[str, tk.BooleanVar] = {}
        self.handle_existing_var = tk.StringVar(value=self.preferences.handle_existing_files)
        self.cancel_event = threading.Event()

        self._build_ui()
        self.refresh_drives()

    def _build_ui(self) -> None:
        drive_frame = ttk.LabelFrame(self.root, text="Mounted Drives")
        drive_frame.pack(fill="x", padx=12, pady=6)

        self.drive_list = tk.Listbox(drive_frame, height=5)
        self.drive_list.pack(side=tk.LEFT, fill="both", expand=True, padx=6, pady=6)
        self.drive_list.bind("<<ListboxSelect>>", lambda _evt: self._on_drive_selected())

        scroll = ttk.Scrollbar(drive_frame, orient="vertical", command=self.drive_list.yview)
        scroll.pack(side=tk.RIGHT, fill="y")
        self.drive_list.config(yscrollcommand=scroll.set)

        destination_frame = ttk.Frame(self.root)
        destination_frame.pack(fill="x", padx=12, pady=6)
        ttk.Label(destination_frame, text="Destination:").pack(side=tk.LEFT)
        ttk.Entry(destination_frame, textvariable=self.destination_var, width=50).pack(side=tk.LEFT, padx=6, fill="x", expand=True)
        ttk.Button(destination_frame, text="Browse", command=self._browse_destination).pack(side=tk.LEFT)

        options_frame = ttk.LabelFrame(self.root, text="Sync Options")
        options_frame.pack(fill="x", padx=12, pady=6)
        self.option_vars = {
            "preserve_permissions": tk.BooleanVar(value=self.preferences.preserve_permissions),
            "preserve_timestamps": tk.BooleanVar(value=self.preferences.preserve_timestamps),
            "include_hidden_files": tk.BooleanVar(value=self.preferences.include_hidden_files),
            "follow_symlinks": tk.BooleanVar(value=self.preferences.follow_symlinks),
        }

        ttk.Checkbutton(options_frame, text="Preserve permissions", variable=self.option_vars["preserve_permissions"]).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Preserve timestamps", variable=self.option_vars["preserve_timestamps"]).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Include hidden files", variable=self.option_vars["include_hidden_files"]).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Follow symlinks", variable=self.option_vars["follow_symlinks"]).pack(anchor="w")

        existing_frame = ttk.Frame(options_frame)
        existing_frame.pack(fill="x", pady=4)
        ttk.Label(existing_frame, text="When destination exists:").pack(side=tk.LEFT)
        ttk.Radiobutton(existing_frame, text="Overwrite", value="overwrite", variable=self.handle_existing_var).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(existing_frame, text="Skip", value="skip", variable=self.handle_existing_var).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(existing_frame, text="Update", value="update", variable=self.handle_existing_var).pack(side=tk.LEFT, padx=4)

        progress_frame = ttk.LabelFrame(self.root, text="Progress")
        progress_frame.pack(fill="x", padx=12, pady=6)
        ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100).pack(fill="x", padx=6, pady=6)
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor="w", padx=6)

        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=12, pady=6)
        ttk.Button(action_frame, text="Start Sync", command=self.start_sync).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Cancel", command=self.cancel_sync).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_frame, text="Refresh Drives", command=self.refresh_drives).pack(side=tk.RIGHT)

    def _browse_destination(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.destination_var.set(selected)

    def _on_drive_selected(self) -> None:
        if not self.drive_list:
            return
        selection = self.drive_list.curselection()
        if not selection:
            return
        drive_name = self.drive_list.get(selection[0])
        drive_path = Path("/Volumes") / drive_name
        self.destination_var.set(str(drive_path))

    def refresh_drives(self) -> None:
        drives = self.detector.enumerate_drives()
        self.drive_list.delete(0, tk.END)
        for drive in drives:
            self.drive_list.insert(tk.END, drive.name)
        if not drives:
            messagebox.showinfo("No Drives", "No writable mounted drives detected.")

    def start_sync(self) -> None:
        if not self.sources:
            self._show_error("No source files received from Quick Action.")
            return

        destination = Path(self.destination_var.get())
        permission_result = validate_destination(destination)
        if not permission_result.allowed:
            self._show_error(permission_result.reason or "Destination is not writable.")
            return

        options = SyncOptions(
            preserve_permissions=self.option_vars["preserve_permissions"].get(),
            preserve_timestamps=self.option_vars["preserve_timestamps"].get(),
            include_hidden_files=self.option_vars["include_hidden_files"].get(),
            follow_symlinks=self.option_vars["follow_symlinks"].get(),
            handle_existing_files=self.handle_existing_var.get(),
        )

        self.preferences_store.save(
            UserPreferences(
                preserve_permissions=options.preserve_permissions,
                preserve_timestamps=options.preserve_timestamps,
                include_hidden_files=options.include_hidden_files,
                follow_symlinks=options.follow_symlinks,
                handle_existing_files=options.handle_existing_files,
            )
        )

        try:
            command = self.command_builder.build(self.sources, destination, options)
        except Exception as exc:
            self._show_error(str(exc))
            return

        self.status_var.set("Starting...")
        self.progress_var.set(0.0)
        self.cancel_event.clear()

        threading.Thread(target=self._run_rsync, args=(command,), daemon=True).start()

    def cancel_sync(self) -> None:
        self.cancel_event.set()
        self.status_var.set("Cancelling...")

    def _run_rsync(self, command: list[str]) -> None:
        def on_progress(progress: dict) -> None:
            percent = progress.get("percent")
            if percent is not None:
                self.root.after(0, self.progress_var.set, percent)
                self.root.after(0, self.status_var.set, f"Syncing... {percent:.0f}%")

        result = self.runner.run(command, on_progress=on_progress, cancel_event=self.cancel_event)
        if result.cancelled:
            self.root.after(0, self.status_var.set, "Cancelled")
        elif result.success:
            self.root.after(0, self.status_var.set, "Completed")
            messagebox.showinfo("Rsync", "Synchronization completed successfully.")
        else:
            self.root.after(0, self.status_var.set, "Failed")
            error_output = "\n".join(result.errors or result.output)
            self._show_error(f"Rsync failed. {error_output}")

    def run(self) -> None:
        self.root.mainloop()

    def _show_error(self, message: str) -> None:
        messagebox.showerror("Error", message)
