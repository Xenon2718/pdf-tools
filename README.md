# pdf-tools

A lightweight desktop PDF utility built with Tkinter and Python's standard library.

## Features

- Add one or more PDF files to a queue
- Optionally drag and drop PDFs when `tkinterdnd2` is installed
- Use the empty file-list area to drag and drop PDFs, or choose **Add Files**
- View each file's type, size, added time, modified time, and page count
- See the total number and combined size of queued PDFs
- Reorder files before merging with Move Up and Move Down
- Merge multiple PDFs into a single file
- Split a selected PDF into two parts
- Clear and manage the current selection

The merge operation processes files from top to bottom in the selected-files list.
Use **Refresh Details** to update size, modified time, and page count if a PDF changes while it is queued.

The app starts without third-party packages. PDF merging and splitting require the optional
`pypdf` package; drag and drop requires the optional `tkinterdnd2` package. Without
`tkinterdnd2`, use **Add Files** to select PDFs.

To enable the optional features, install only the package(s) you need:

```bash
python -m pip install pypdf
python -m pip install tkinterdnd2
```

## Run

```bash
python main.py
```
