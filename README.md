# Starfield BA2 Manager & Compressor

A lightweight, cross-platform tool (Linux / Windows) written in Python with a graphical user interface (Tkinter) for managing, viewing, exporting, and creating BA2 archives for Starfield.

## 🚀 Key Features
* **Full BA2 Support:** Parses standard `General` and texture `Texture (DX10)` archives with robust handling for unconventional or fallback names.
* **Browse & Inspect:** Clean file tree view showing internal structure, file sizes, and exact archive offsets.
* **Export / Extract:** Extract selected files or unpack the entire archive with a single click.
* **Archive Creation:** Pack a custom folder of files into a new `.ba2` archive (supporting both `General` and `Texture (DX10)` compression modes).
* **Drag & Drop Support:** Drop `.ba2` files directly into the application window (requires the optional `tkinterdnd2` package).
* **Cross-Platform:** Works seamlessly on Linux distributions (Ubuntu, Fedora, etc.) and Windows.

---

## 📦 Installation & Requirements

### Prerequisites
* **Python 3.8+**

### Optional Dependencies (for Drag & Drop)
If you want drag-and-drop functionality, install the `tkinterdnd2` library via pip:
```bash
pip install tkinterdnd2

🛠️ Usage

Clone or download the repository, then run the script from your terminal or command prompt:
Bash

python ba2_gui.py

    Open an Archive: Click 📂 Open BA2 (or drag and drop a .ba2 file into the window) and select an archive from your Starfield directory.

    Browse: View the internal path structure and file properties in the main list.

    Extract:

        Select specific files and click Export Selected.

        Or click Export All to unpack the entire archive.

    Create a New BA2:

        Under the Archive Compression Settings panel, browse to select your Source folder.

        Enter the path and file name for the Output BA2 (Destination).

        Choose the compression method (General or Texture (DX10)) and click 📦 Create / Pack BA2.

🐞 Debugging

The application automatically generates a log file named ba2_gui_debug.log in the same directory as the script. Check this file if you encounter any unexpected issues.
📜 License

This project is open-source, available under the MIT License.
