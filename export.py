"""
Export Module

Export functionality for proxy management application.
Provides a GUI to filter, select and export proxy data in various formats.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv


def sort_by_column(tv, col, reverse):
    """
    Sort treeview data based on the selected column.

    Args:
        tv: Treeview widget
        col: Column identifier to sort by
        reverse: Boolean indicating whether to sort in reverse order
    """
    data = [(tv.set(k, col), k) for k in tv.get_children("")]
    try:
        # Try numeric sorting first
        data.sort(key=lambda t: float(t[0]), reverse=reverse)
    except ValueError:
        # Fall back to string sorting
        data.sort(key=lambda t: t[0], reverse=reverse)

    # Rearrange items in sorted positions
    for index, (_, k) in enumerate(data):
        tv.move(k, "", index)

    # Configure the heading command to reverse sort on next click
    tv.heading(col, command=lambda: sort_by_column(tv, col, not reverse))


def open_export_window(tree, results):
    """
    Open a window to filter and export proxy data.

    Args:
        tree: Original treeview widget containing proxy data
        results: List of proxy data rows
    """
    original_rows = results

    # Create and configure export window
    win = tk.Toplevel()
    win.title("Filter & Export Proxies")
    win.geometry("950x1050")

    # Track current sort state
    sort_col = None
    sort_reverse = False

    # Create filter frame for controls
    filter_frame = ttk.Frame(win, padding=5)
    filter_frame.pack(fill="x")

    # Define checkbox display characters
    # TODO: Find way to make it look better, janky but works
    unchecked, checked = "☐", "☑"

    # Track selected rows with a set for O(1) lookups
    selected_iids = set()

    # Select All checkbox functionality
    select_all_var = tk.BooleanVar(value=False)

    def on_select_all():
        """Toggle selection state for all visible rows"""
        for iid in export_tree.get_children():
            if select_all_var.get():
                selected_iids.add(iid)
                export_tree.item(iid, tags=("selected",))
                export_tree.set(iid, 'Select', checked)
            else:
                selected_iids.discard(iid)
                export_tree.item(iid, tags=())
                export_tree.set(iid, 'Select', unchecked)
        update_status()

    ttk.Checkbutton(filter_frame, text="Select All", variable=select_all_var, command=on_select_all).pack(side="left",
                                                                                                          padx=(0, 5))

    # Clear Selected button functionality
    def on_clear_selected():
        """Clear all selections"""
        for iid in list(selected_iids):
            selected_iids.discard(iid)
            export_tree.item(iid, tags=())
            export_tree.set(iid, 'Select', unchecked)
        select_all_var.set(False)
        update_status()

    ttk.Button(filter_frame, text="Clear Selected", command=on_clear_selected).pack(side="left", padx=(0, 15))

    # Fraud score filter control
    ttk.Label(filter_frame, text="Max Fraud Score:").pack(side="left")
    max_fs_var = tk.StringVar(value="100")

    def on_validate(P):
        """Validate input for fraud score (0-100 range)"""
        return P == "" or (P.isdigit() and 0 <= int(P) <= 100)

    vcmd = (win.register(on_validate), '%P')
    fs_spin = tk.Spinbox(filter_frame, from_=0, to=100, width=5, textvariable=max_fs_var,
                         validate='key', validatecommand=vcmd)
    fs_spin.pack(side="left", padx=(0, 15))

    # Prevent default Enter key behavior
    fs_spin.bind('<Return>', lambda e: 'break')

    # Auto-refresh on value change
    max_fs_var.trace_add("write", lambda *a: refresh())

    # Boolean column filters (Proxy, VPN, etc.)
    bool_cols = ["Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]
    bool_vars = {}
    for col in bool_cols:
        ttk.Label(filter_frame, text=col + ":").pack(side="left")
        var = tk.StringVar(value="All")
        cb = ttk.Combobox(filter_frame, textvariable=var,
                          values=["All", "True", "False"], width=8, state="readonly")
        cb.pack(side="left", padx=(0, 10))

        # Auto-refresh on selection change
        var.trace_add("write", lambda *a: refresh())
        bool_vars[col] = var

    # Configure export treeview
    cols = list(tree["columns"])
    display_cols = ["Select"] + cols
    export_tree = ttk.Treeview(win, columns=display_cols, show="headings", selectmode="none")

    # For shift-click range selection
    last_iid = None

    # Configure the 'selected' row appearance
    export_tree.tag_configure("selected", background="#b3cbff")

    # Configure columns and capture sort state
    for col in display_cols:
        if col == "Select":
            export_tree.heading(col, text=col)
            export_tree.column(col, width=50, anchor="center")
        else:
            def handler(c=col):
                """Column header click handler for sorting"""
                nonlocal sort_col, sort_reverse
                sort_by_column(export_tree, c, sort_reverse)
                sort_col, sort_reverse = c, not sort_reverse

            export_tree.heading(col, text=col, command=handler)
            export_tree.column(col, width=tree.column(col, option="width"))
    export_tree.pack(fill="both", expand=True, pady=5, padx=5)

    # Status bar to display selection count
    status_var = tk.StringVar()
    status_label = ttk.Label(win, textvariable=status_var, anchor='w', font=('Helvetica', 10, 'italic'))
    status_label.pack(side='bottom', fill='x', padx=5, pady=2)

    def update_status():
        """Update the status bar with current selection info"""
        total = len(export_tree.get_children())
        selected = len(selected_iids)
        status_var.set(f"Selected: {selected} / {total}")

    # Row click handler for selection toggling
    def on_tree_click(event):
        """Handle row click to toggle selection state"""
        nonlocal last_iid
        iid = export_tree.identify_row(event.y)
        if not iid:
            return

        # Support shift-click for range selection
        if event.state & 0x0001 and last_iid and iid != last_iid:
            children = export_tree.get_children()
            start = children.index(last_iid)
            end = children.index(iid)
            for j in children[min(start, end):max(start, end) + 1]:
                selected_iids.add(j)
                export_tree.item(j, tags=("selected",))
                export_tree.set(j, 'Select', checked)
        else:
            # Toggle single row selection
            if iid in selected_iids:
                selected_iids.remove(iid)
                export_tree.item(iid, tags=())
                export_tree.set(iid, 'Select', unchecked)
            else:
                selected_iids.add(iid)
                export_tree.item(iid, tags=("selected",))
                export_tree.set(iid, 'Select', checked)

        last_iid = iid

        # Update "Select All" checkbox state based on selection
        select_all_var.set(all(i in selected_iids for i in export_tree.get_children()))
        update_status()

    export_tree.bind("<Button-1>", on_tree_click)

    # Keyboard shortcuts
    def on_ctrl_a(event):
        """Handle Ctrl+A to select all rows"""
        select_all_var.set(True)
        on_select_all()
        update_status()
        return "break"  # Prevent default behavior

    export_tree.bind("<Control-a>", on_ctrl_a)
    export_tree.bind("<Control-A>", on_ctrl_a)

    def refresh():
        """
        Refresh the treeview with filtered data.
        Applies all active filters and repopulates the export tree.
        """
        export_tree.delete(*export_tree.get_children())
        selected_iids.clear()

        for idx, full_row in enumerate(original_rows):
            # Apply fraud score filter
            try:
                max_val = int(max_fs_var.get()) if max_fs_var.get() != "" else 0
            except ValueError:
                max_val = 0

            if full_row[4] > max_val:
                continue

            # Apply boolean filters (proxy, VPN, etc.)
            ok = True
            for col, var in bool_vars.items():
                v = var.get()
                if v != "All" and str(full_row[cols.index(col)]) != v:
                    ok = False
                    break

            if not ok:
                continue

            # Insert row that passes all filters
            export_tree.insert("", tk.END, iid=str(idx),
                               values=[checked if select_all_var.get() else unchecked] + full_row[:-1],
                               tags=("selected",) if select_all_var.get() else ())

            if select_all_var.get():
                selected_iids.add(str(idx))

        # Reapply last sort if active
        if sort_col:
            sort_by_column(export_tree, sort_col, not sort_reverse)

        update_status()

    # Initial data load
    refresh()

    # Column selection for export format
    column_frame = ttk.LabelFrame(win, text="CSV Format Columns", padding=10)
    column_frame.pack(fill="x", padx=5, pady=5)

    # Define available columns for export
    column_vars = {}
    column_names = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
                    "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    # Create a grid of checkboxes for column selection
    col_checkboxes_frame = ttk.Frame(column_frame)
    col_checkboxes_frame.pack(fill="x", expand=True)

    for i, col_name in enumerate(column_names):
        # All selected by default
        var = tk.BooleanVar(value=True)

        column_vars[col_name] = var
        cb = ttk.Checkbutton(col_checkboxes_frame, text=col_name, variable=var)

        # 3 columns of checkboxes
        row, col = divmod(i, 3)
        cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)

    # Buttons to select/deselect all columns
    col_btn_frame = ttk.Frame(column_frame)
    col_btn_frame.pack(fill="x", pady=(10, 0))

    def select_all_columns():
        """Select all export columns"""
        for var in column_vars.values():
            var.set(True)

    def deselect_all_columns():
        """Deselect all export columns"""
        for var in column_vars.values():
            var.set(False)

    ttk.Button(col_btn_frame, text="Select All Columns", command=select_all_columns).pack(side="left", padx=5)
    ttk.Button(col_btn_frame, text="Deselect All Columns", command=deselect_all_columns).pack(side="left")

    # Export format selection frame
    format_frame = ttk.LabelFrame(win, text="Export Format", padding=10)
    format_frame.pack(fill="x", padx=5, pady=5)

    format_var = tk.StringVar(value="txt")
    ttk.Radiobutton(format_frame, text="Raw Text Format", variable=format_var, value="txt").pack(anchor="w")
    ttk.Radiobutton(format_frame, text="CSV Format", variable=format_var, value="csv").pack(anchor="w")

    # Template configuration for text format
    template_frame = ttk.LabelFrame(format_frame, text="Raw Text Format Template", padding=5)
    template_frame.pack(fill="x", pady=(5, 0), expand=True)

    # Default template pattern
    template_var = tk.StringVar(value="{Proxy IP}:{Port}:{Username}:{Password}")
    template_entry = ttk.Entry(template_frame, textvariable=template_var, width=60)
    template_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    # Help button with template placeholders
    def show_template_help():
        """Show dialog with template placeholder information"""
        help_text = (
            "Available placeholders:\n"
            "{Proxy IP} - Proxy IP address\n"
            "{Public IP} - Public IP\n"
            "{Location} - Location\n"
            "{ISP} - ISP\n"
            "{Fraud Score} - Fraud Score\n"
            "{Proxy} - Is Proxy\n"
            "{VPN} - Is VPN\n"
            "{Tor} - Is Tor\n"
            "{Mobile} - Is Mobile\n"
            "{Recent Abuse} - Recent Abuse\n"
            "{Bot Status} - Bot Status\n"
            "{Port} - Port number\n"
            "{Username} - Username\n"
            "{Password} - Password\n\n"
            "Example: {Proxy IP}:{Port}:{Username}:{Password}"
        )
        messagebox.showinfo("Template Help", help_text)

    ttk.Button(template_frame, text="?", width=3, command=show_template_help).pack(side="right")

    # Button frame for export/cancel actions
    btn_frame = ttk.Frame(win, padding=5)
    btn_frame.pack(fill="x")

    def do_export():
        """
        Perform the export operation with selected format and options.
        Validates selections and exports to user-selected file.
        """
        # Validate selections
        if not selected_iids:
            messagebox.showinfo("No selection", "Select at least one proxy.")
            return

        selected_columns = [col for col in column_names if column_vars[col].get()]
        if not selected_columns and format_var.get() == "csv":
            messagebox.showinfo("No columns", "Select at least one column to export.")
            return

        # Configure save file dialog
        default_ext = "." + format_var.get()
        filetypes = [("All Files", "*.*")]

        path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=filetypes,
            initialfile=f"proxy_export{default_ext}"
        )

        if not path:
            # User canceled
            return

        export_format = path.split('.')[-1].lower()

        if export_format == "csv":
            # CSV export logic
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header row
                writer.writerow(selected_columns)

                # Write data rows
                for iid in selected_iids:
                    row = original_rows[int(iid)]

                    # Extract credentials from details string
                    details_dict = {}
                    details_text = row[-1]  # Get the details string
                    for line in details_text.splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            details_dict[key.strip()] = value.strip()

                    # Create a row with only selected columns
                    output_row = []
                    for i, col in enumerate(column_names):
                        if col in selected_columns:
                            output_row.append(row[i])

                    writer.writerow(output_row)

            count = len(selected_iids)
            messagebox.showinfo("Export Complete", f"Exported {count} proxies to CSV file.")

        else:
            # Text export with template
            template = template_var.get()
            if not template:
                template = "{Proxy IP}:{Port}:{Username}:{Password}"  # Default

            with open(path, "w", encoding="utf-8") as f:
                for iid in selected_iids:
                    row = original_rows[int(iid)]

                    # Create a mapping of placeholders to values
                    values_dict = {}

                    # Add all standard columns
                    for i, col in enumerate(column_names):
                        values_dict[col] = row[i]

                    # Extract credentials from details
                    details_text = row[-1]
                    for line in details_text.splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            values_dict[key.strip()] = value.strip()

                    # Replace placeholders in template with values
                    line = template
                    for key, value in values_dict.items():
                        line = line.replace("{" + key + "}", str(value))

                    f.write(line + "\n")

            count = len(selected_iids)
            messagebox.showinfo("Export Complete", f"Exported {count} proxies to text file.")

        # Close export window after successful export
        win.destroy()

    # Add action buttons
    ttk.Button(btn_frame, text="Export Selected", command=do_export).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="right")