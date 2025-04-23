"""
Export Module

This module handles exporting proxy check results to different formats
and provides functionality for filtering and selecting proxies before export.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv

from utils import sort_by_column


def export_to_csv(results):
    """
    Export proxy check results to a CSV file.

    Args:
        results (list): List of proxy check results
    """
    if not results:
        messagebox.showinfo("Export", "No data to export.")
        return

    # Get file save location from user
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    headers = ["Proxy IP", "Public IP", "Location", "ISP", "Fraud Score",
               "Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]

    # Write data to CSV file
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for row in results:
            writer.writerow(row[:-1])  # exclude details column

    messagebox.showinfo("Export Complete", f"Data successfully exported to\n{file_path}")


def open_export_window(tree, results):
    """
    Open an advanced export window with filtering and selection capabilities.

    Args:
        tree (ttk.Treeview): The main application's Treeview with proxy data
        results (list): List of proxy check results
    """
    original_rows = results

    # Create export window
    win = tk.Toplevel()
    win.title("Filter & Export Proxies")
    win.geometry("950x580")  # slightly taller for status bar

    # Track current sort state
    sort_col = None
    sort_reverse = False

    # Create filter frame at top
    filter_frame = ttk.Frame(win, padding=5)
    filter_frame.pack(fill="x")

    # Create checkbox symbols and data structures for selection tracking
    unchecked, checked = "☐", "☑"
    selected_iids = set()  # Set of selected item IDs
    last_iid = None  # For shift-selection

    def update_status():
        """Update the status bar with selection counts"""
        total = len(export_tree.get_children())
        selected = len(selected_iids)
        status_var.set(f"Selected: {selected} / {total}")

    # === Selection controls ===

    # Select All checkbox
    select_all_var = tk.BooleanVar(value=False)

    def on_select_all():
        """Handle selection or deselection of all items"""
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

    # Clear Selected button
    def on_clear_selected():
        """Clear all selections"""
        for iid in list(selected_iids):
            selected_iids.discard(iid)
            export_tree.item(iid, tags=())
            export_tree.set(iid, 'Select', unchecked)
        select_all_var.set(False)
        update_status()

    ttk.Button(filter_frame, text="Clear Selected", command=on_clear_selected).pack(side="left", padx=(0, 15))

    # === Filters ===

    # Fraud Score filter
    ttk.Label(filter_frame, text="Max Fraud Score:").pack(side="left")
    max_fs_var = tk.StringVar(value="100")

    # Validate function for fraud score input
    def on_validate(P):
        """Validate that fraud score input is a number between 0-100"""
        return P == "" or (P.isdigit() and 0 <= int(P) <= 100)

    vcmd = (win.register(on_validate), '%P')
    fs_spin = tk.Spinbox(filter_frame, from_=0, to=100, width=5, textvariable=max_fs_var,
                         validate='key', validatecommand=vcmd)
    fs_spin.pack(side="left", padx=(0, 15))
    fs_spin.bind('<Return>', lambda e: 'break')  # Prevent Enter from triggering unwanted actions

    # Refresh function to update the view based on filters
    def refresh(*args):
        """Refresh the treeview with filtered results"""
        export_tree.delete(*export_tree.get_children())
        selected_iids.clear()
        cols = list(tree["columns"])

        # Apply filters to each row
        for idx, full_row in enumerate(original_rows):
            # Apply fraud score filter
            try:
                max_val = int(max_fs_var.get()) if max_fs_var.get() != "" else 0
            except ValueError:
                max_val = 0
            if full_row[4] > max_val:
                continue

            # Apply boolean filters (Proxy, VPN, etc.)
            ok = True
            for col, var in bool_vars.items():
                v = var.get()
                if v != "All" and str(full_row[cols.index(col)]) != v:
                    ok = False
                    break
            if not ok:
                continue

            # Add filtered row to tree
            export_tree.insert("", tk.END, iid=str(idx),
                               values=[checked if select_all_var.get() else unchecked] + full_row[:-1],
                               tags=("selected",) if select_all_var.get() else ())
            if select_all_var.get():
                selected_iids.add(str(idx))

        # Reapply last sort if any
        if sort_col:
            sort_by_column(export_tree, sort_col, not sort_reverse)
        update_status()

    # Connect fraud score changes to refresh
    max_fs_var.trace_add("write", refresh)

    # Boolean filters (True/False/All dropdowns)
    bool_cols = ["Proxy", "VPN", "Tor", "Mobile", "Recent Abuse", "Bot Status"]
    bool_vars = {}
    for col in bool_cols:
        ttk.Label(filter_frame, text=col + ":").pack(side="left")
        var = tk.StringVar(value="All")
        cb = ttk.Combobox(filter_frame, textvariable=var,
                          values=["All", "True", "False"], width=8, state="readonly")
        cb.pack(side="left", padx=(0, 10))
        var.trace_add("write", refresh)  # Connect filter changes to refresh
        bool_vars[col] = var

    # === Setup Treeview for displaying filtered results ===
    cols = list(tree["columns"])
    display_cols = ["Select"] + cols
    export_tree = ttk.Treeview(win, columns=display_cols, show="headings", selectmode="none")

    # Configure selection highlighting
    export_tree.tag_configure("selected", background="#b3cbff")

    # Configure columns and capture sort state
    for col in display_cols:
        if col == "Select":
            export_tree.heading(col, text=col)
            export_tree.column(col, width=50, anchor="center")
        else:
            def handler(c=col):
                """Handle column click for sorting"""
                nonlocal sort_col, sort_reverse
                sort_by_column(export_tree, c, sort_reverse)
                sort_col, sort_reverse = c, not sort_reverse

            export_tree.heading(col, text=col, command=handler)
            export_tree.column(col, width=tree.column(col, option="width"))
    export_tree.pack(fill="both", expand=True, pady=5, padx=5)

    # Status bar at bottom
    status_var = tk.StringVar()
    status_label = ttk.Label(win, textvariable=status_var, anchor='w', font=('Helvetica', 10, 'italic'))
    status_label.pack(side='bottom', fill='x', padx=5, pady=2)

    # === Event handlers for selection ===

    # Handle row click for selection
    def on_tree_click(event):
        """Handle mouse click on tree rows for selection"""
        nonlocal last_iid
        iid = export_tree.identify_row(event.y)
        if not iid:
            return

        # Handle shift+click for range selection
        if event.state & 0x0001 and last_iid and iid != last_iid:
            children = export_tree.get_children()
            start = children.index(last_iid)
            end = children.index(iid)
            for j in children[min(start, end):max(start, end) + 1]:
                selected_iids.add(j)
                export_tree.item(j, tags=("selected",))
                export_tree.set(j, 'Select', checked)
        else:
            # Toggle single item selection
            if iid in selected_iids:
                selected_iids.remove(iid)
                export_tree.item(iid, tags=())
                export_tree.set(iid, 'Select', unchecked)
            else:
                selected_iids.add(iid)
                export_tree.item(iid, tags=("selected",))
                export_tree.set(iid, 'Select', checked)
        last_iid = iid

        # Update select all checkbox state
        select_all_var.set(all(i in selected_iids for i in export_tree.get_children()))
        update_status()

    export_tree.bind("<Button-1>", on_tree_click)

    # Handle Ctrl+A for select all
    def on_ctrl_a(event):
        """Handle Ctrl+A keyboard shortcut to select all"""
        select_all_var.set(True)
        on_select_all()
        update_status()
        return "break"  # Prevent default behavior

    export_tree.bind("<Control-a>", on_ctrl_a)
    export_tree.bind("<Control-A>", on_ctrl_a)

    # Initial refresh to populate the tree
    refresh()

    # === Button frame for actions ===
    btn_frame = ttk.Frame(win, padding=5)
    btn_frame.pack(fill="x")

    def do_export():
        """Export selected proxies to a file"""
        if not selected_iids:
            messagebox.showinfo("No selection", "Select at least one proxy.")
            return

        # Get file path from user
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt"), ("CSV", "*.csv")])
        if not path:
            return

        # Write selected proxies to file
        with open(path, "w", newline="") as f:
            for iid in selected_iids:
                row = original_rows[int(iid)]
                ip = row[0]
                # Parse details into a dictionary
                parts = dict(line.split(":", 1) for line in row[-1].splitlines())
                # Format as IP:PORT:USER:PASS
                line = f"{ip}:{parts['Port'].strip()}:{parts['Username'].strip()}:{parts['Password'].strip()}"
                f.write(line + "\n")

        messagebox.showinfo("Exported", f"Wrote {len(selected_iids)} proxies to {path}")
        win.destroy()

    # Add export and cancel buttons
    ttk.Button(btn_frame, text="Export Selected", command=do_export).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="right")