import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - handled at runtime
    DND_FILES = None
    TkinterDnD = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover - handled at runtime
    PdfReader = None
    PdfWriter = None


_TkBase = TkinterDnD.Tk if TkinterDnD is not None else tk.Tk


class PDFToolsApp(_TkBase):
    def __init__(self):
        super().__init__()
        self.title("PDF Tools")
        self.geometry("960x640")
        self.minsize(780, 480)
        self.app_icon = self.create_app_icon()
        self.iconphoto(True, self.app_icon)
        self.selected_files = []
        self.file_details = {}
        self.create_widgets()
        self.configure_drag_and_drop()

    @staticmethod
    def create_app_icon():
        icon = tk.PhotoImage(width=32, height=32)

        def rectangle(color, x1, y1, x2, y2):
            icon.put(color, to=(x1, y1, x2, y2))

        rectangle("#8eb7d8", 4, 5, 23, 29)
        rectangle("#d5e5f1", 6, 4, 25, 28)
        rectangle("#ffffff", 8, 3, 27, 27)
        rectangle("#c8d8e5", 8, 3, 27, 5)
        rectangle("#c62828", 10, 10, 24, 17)
        rectangle("#ffffff", 12, 12, 14, 13)
        rectangle("#ffffff", 16, 12, 18, 13)
        rectangle("#ffffff", 20, 12, 22, 13)
        rectangle("#d5e0e8", 11, 20, 24, 21)
        rectangle("#d5e0e8", 11, 23, 22, 24)
        rectangle("#d5e0e8", 11, 26, 20, 27)
        return icon

    def create_widgets(self):
        self.main = ttk.Frame(self, padding=20)
        self.main.pack(fill="both", expand=True)

        title = ttk.Label(self.main, text="PDF Tools", font=("Segoe UI", 24, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        subtitle = ttk.Label(
            self.main,
            text="Combine, organize, and split PDFs with a simple desktop workflow.",
        )
        subtitle.pack(anchor="w", pady=(0, 18))

        toolbar = ttk.Frame(self.main)
        toolbar.pack(fill="x", pady=(0, 12))

        ttk.Button(toolbar, text="Add Files", command=self.add_files).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Clear List", command=self.clear_files).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Merge PDFs", command=self.merge_selected).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Split PDF", command=self.split_selected_pdf).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="About", command=self.show_about).pack(side="left")

        list_frame = ttk.LabelFrame(self.main, text="Selected Files — merge order", padding=(12, 8))
        list_frame.pack(fill="both", expand=True)

        columns = ("order", "name", "extension", "size", "added", "modified", "pages")
        self.file_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            height=14,
        )
        headings = {
            "order": "#",
            "name": "File name",
            "extension": "Type",
            "size": "Size",
            "added": "Added to app",
            "modified": "Last modified",
            "pages": "Pages",
        }
        widths = {
            "order": 45,
            "name": 240,
            "extension": 65,
            "size": 85,
            "added": 135,
            "modified": 135,
            "pages": 70,
        }
        for column in columns:
            self.file_list.heading(column, text=headings[column])
            self.file_list.column(
                column,
                width=widths[column],
                minwidth=40 if column == "order" else 65,
                anchor="center" if column in ("order", "extension", "size", "pages") else "w",
                stretch=column == "name",
            )

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        self.file_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.drop_zone = tk.Frame(
            list_frame,
            bg="#edf1f5",
            highlightbackground="#cbd3dc",
            highlightthickness=1,
        )
        drop_zone_text = "Or drag and drop PDF files here"
        if DND_FILES is None:
            drop_zone_text = "Add Files to select PDFs"
        self.drop_zone_label = tk.Label(
            self.drop_zone,
            text=drop_zone_text,
            bg="#edf1f5",
            fg="#586575",
            font=("Segoe UI", 11),
        )
        self.drop_zone_label.pack(fill="both", expand=True)
        self.drop_zone.place(relx=0, rely=0, relwidth=1, relheight=1)

        order_controls = ttk.Frame(self.main)
        order_controls.pack(fill="x", pady=(8, 0))
        ttk.Button(order_controls, text="Move Up", command=lambda: self.move_selected(-1)).pack(side="left", padx=(0, 8))
        ttk.Button(order_controls, text="Move Down", command=lambda: self.move_selected(1)).pack(side="left")
        ttk.Button(order_controls, text="Refresh Details", command=self.refresh_details).pack(side="left", padx=(8, 0))

        ttk.Label(self.main, text="Use Move Up / Move Down to set merge order.").pack(anchor="w", pady=(6, 0))

        self.summary_var = tk.StringVar(value="0 PDFs selected  •  Total size: 0 B")
        ttk.Label(self.main, textvariable=self.summary_var).pack(anchor="w", pady=(8, 0))
        self.status_var = tk.StringVar(value="Ready. Add or drop PDF files to begin.")
        status = ttk.Label(self.main, textvariable=self.status_var)
        status.pack(anchor="w", pady=(4, 0))

    def configure_drag_and_drop(self):
        if DND_FILES is None:
            return

        self.file_list.drop_target_register(DND_FILES)
        self.file_list.dnd_bind("<<Drop>>", self.handle_file_drop)
        for widget in (self.drop_zone, self.drop_zone_label):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.handle_file_drop)

    def handle_file_drop(self, event):
        dropped_files = self.tk.splitlist(event.data)
        pdf_files = [path for path in dropped_files if path.lower().endswith(".pdf")]
        rejected_count = len(dropped_files) - len(pdf_files)
        self.add_pdf_files(pdf_files)

        if rejected_count:
            self.status_var.set(f"{self.status_var.get()} Ignored {rejected_count} non-PDF file(s).")

    def add_pdf_files(self, files):
        added_count = 0
        rejected_count = 0
        for file_path in files:
            if not file_path.lower().endswith(".pdf"):
                rejected_count += 1
            elif file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.file_details[file_path] = self.read_file_details(file_path)
                added_count += 1

        self.refresh_list()
        message = f"Added {added_count} PDF file(s). {len(self.selected_files)} total selected."
        if rejected_count:
            message += f" Ignored {rejected_count} non-PDF file(s)."
        self.status_var.set(message)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select PDF files",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not files:
            return

        self.add_pdf_files(files)

    def refresh_list(self):
        self.file_list.delete(*self.file_list.get_children())
        total_size = 0
        for index, file_path in enumerate(self.selected_files):
            details = self.file_details.get(file_path, {})
            size = details.get("size_bytes")
            if size is not None:
                total_size += size

            self.file_list.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index + 1,
                    os.path.basename(file_path),
                    os.path.splitext(file_path)[1].lower() or "—",
                    self.format_size(size),
                    details.get("added", "—"),
                    details.get("modified", "—"),
                    details.get("pages", "—"),
                ),
            )

        if self.selected_files:
            self.drop_zone.place_forget()
        else:
            self.drop_zone.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.summary_var.set(
            f"{len(self.selected_files)} PDF(s) selected  •  Total size: {self.format_size(total_size)}"
        )

    @staticmethod
    def format_size(size_bytes):
        if size_bytes is None:
            return "Unavailable"
        if size_bytes < 1024:
            return f"{size_bytes} B"

        size = float(size_bytes)
        for unit in ("KB", "MB", "GB", "TB"):
            size /= 1024
            if size < 1024 or unit == "TB":
                return f"{size:.1f} {unit}"
        return f"{size_bytes} B"

    @staticmethod
    def read_file_details(file_path):
        details = {
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modified": "Unavailable",
            "size_bytes": None,
            "pages": "Unavailable",
        }
        try:
            file_stat = os.stat(file_path)
            details["size_bytes"] = file_stat.st_size
            details["modified"] = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            return details

        if PdfReader is None:
            details["pages"] = "Install pypdf"
        else:
            try:
                details["pages"] = len(PdfReader(file_path).pages)
            except Exception:
                details["pages"] = "Unreadable"

        return details

    def refresh_details(self):
        for file_path in self.selected_files:
            previous_added = self.file_details.get(file_path, {}).get("added")
            self.file_details[file_path] = self.read_file_details(file_path)
            self.file_details[file_path]["added"] = previous_added or self.file_details[file_path]["added"]
        self.refresh_list()
        self.status_var.set("File details refreshed.")

    def remove_selected(self):
        selected_indexes = sorted(int(item) for item in self.file_list.selection())
        if not selected_indexes:
            self.status_var.set("Select a file in the list to remove it.")
            return

        for index in reversed(selected_indexes):
            removed_file = self.selected_files.pop(index)
            self.file_details.pop(removed_file, None)

        self.refresh_list()
        self.status_var.set("Selected file(s) removed.")

    def move_selected(self, direction):
        selected_indexes = sorted(int(item) for item in self.file_list.selection())
        if not selected_indexes:
            self.status_var.set("Select one or more files to change their merge order.")
            return

        selected_files = {self.selected_files[index] for index in selected_indexes}
        indexes = selected_indexes if direction < 0 else reversed(selected_indexes)
        moved = False
        for index in indexes:
            new_index = index + direction
            if 0 <= new_index < len(self.selected_files):
                self.selected_files[index], self.selected_files[new_index] = (
                    self.selected_files[new_index],
                    self.selected_files[index],
                )
                moved = True

        if not moved:
            self.status_var.set("The selected file(s) are already at that end of the list.")
            return

        self.refresh_list()
        new_indexes = []
        for index, file_path in enumerate(self.selected_files):
            if file_path in selected_files:
                self.file_list.selection_add(str(index))
                new_indexes.append(index)
        self.file_list.focus(str(min(new_indexes) if direction < 0 else max(new_indexes)))
        self.status_var.set("Merge order updated.")

    def clear_files(self):
        self.selected_files.clear()
        self.file_details.clear()
        self.refresh_list()
        self.status_var.set("File list cleared.")

    def merge_selected(self):
        if not self.selected_files:
            self.status_var.set("Select at least one PDF before merging.")
            return

        if PdfWriter is None:
            self.status_var.set("Install the pypdf package to enable PDF merging.")
            messagebox.showerror(
                "Missing dependency",
                "Install 'pypdf' with: pip install pypdf",
            )
            return

        target = filedialog.asksaveasfilename(
            title="Save merged PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not target:
            return

        writer = PdfWriter()
        try:
            for file_path in self.selected_files:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    writer.add_page(page)

            with open(target, "wb") as output_file:
                writer.write(output_file)

            self.status_var.set(f"Merged PDF saved to: {target}")
        except Exception as exc:  # pragma: no cover - UI-level error handling
            messagebox.showerror("Merge failed", str(exc))
            self.status_var.set("The merge operation failed. Check the selected files and try again.")

    def split_selected_pdf(self):
        if len(self.selected_files) != 1:
            self.status_var.set("Select exactly one PDF to split it into two parts.")
            return

        if PdfReader is None:
            self.status_var.set("Install the pypdf package to enable PDF splitting.")
            messagebox.showerror(
                "Missing dependency",
                "Install 'pypdf' with: pip install pypdf",
            )
            return

        pdf_path = self.selected_files[0]
        folder = filedialog.askdirectory(title="Choose output folder")
        if not folder:
            return

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            midpoint = max(1, total_pages // 2)

            first_writer = PdfWriter()
            second_writer = PdfWriter()

            for index, page in enumerate(reader.pages):
                if index < midpoint:
                    first_writer.add_page(page)
                else:
                    second_writer.add_page(page)

            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            first_path = os.path.join(folder, f"{base_name}-part-1.pdf")
            second_path = os.path.join(folder, f"{base_name}-part-2.pdf")

            with open(first_path, "wb") as first_file:
                first_writer.write(first_file)
            with open(second_path, "wb") as second_file:
                second_writer.write(second_file)

            self.status_var.set(f"Split PDF saved to: {folder}")
        except Exception as exc:  # pragma: no cover - UI-level error handling
            messagebox.showerror("Split failed", str(exc))
            self.status_var.set("The split operation failed. Check the selected PDF and try again.")

    def show_about(self):
        messagebox.showinfo(
            "About PDF Tools",
            "PDF Tools is a lightweight desktop utility for combining and splitting PDF files.",
        )