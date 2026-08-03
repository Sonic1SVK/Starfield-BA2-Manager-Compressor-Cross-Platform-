import os
import sys
import struct
import shutil
import logging
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------------------------------------------------------
# DEBUG LOGGING
# ---------------------------------------------------------------------------
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ba2_gui_debug.log")

logger = logging.getLogger("ba2_gui")
logger.setLevel(logging.DEBUG)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

_file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
_file_handler.setFormatter(_fmt)
logger.addHandler(_file_handler)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(_fmt)
logger.addHandler(_console_handler)

logger.debug("=== Štart ba2_gui.py (Bez Repacku) ===")

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKINTERDND_AVAILABLE = True
except ImportError as e:
    TKINTERDND_AVAILABLE = False
    logger.debug("Modul 'tkinterdnd2' nie je dostupný: %s", e)

TRANSLATIONS = {
    "English": {
        "title": "Starfield BA2 Manager & Compressor (Cross-Platform)",
        "btn_load": "📂 Open BA2",
        "btn_back": "⬅ Back / Up",
        "lbl_no_file": "No archive selected",
        "drop_zone_text": "📥 Drop .ba2 here",
        "compress_panel": " Archive Compression Settings (Archive2 Style) ",
        "lbl_source": "Source folder (Source):",
        "btn_browse": "Browse...",
        "lbl_dest": "Output BA2 (Destination):",
        "btn_save_as": "Save as...",
        "chk_root": "Use root folder",
        "lbl_method": "Method:",
        "btn_compress": "📦 Create / Pack BA2",
        "col_structure": "Internal Structure / File Path",
        "col_size": "Size (bytes)",
        "col_offset": "Archive Offset",
        "btn_extract_all": "Export All",
        "btn_extract_selected": "Export Selected",
        "lbl_drop_hint": "💡 Tip: Install 'tkinterdnd2' via pip for Drag & Drop support.",
        
        "err_invalid_magic": "Invalid BA2 format (missing BTDX header).",
        "err_parse": "Error parsing BA2: {}",
        "err_no_source_files": "Source folder contains no files to pack!",
        "err_select_source": "Please select a valid source folder!",
        "err_select_output": "Please enter the path and name for the output BA2 file!",
        "msg_compressed": "Archive was successfully created:\n{}",
        "msg_loaded": "Loaded {} files (Detected type: {}).",
        "warn_open_first": "Please open a BA2 archive first!",
        "warn_no_selection": "You have no files selected for export!",
        "msg_exported": "Exported {} files.",
        "msg_exported_all": "All files exported."
    },
    "Slovenčina": {
        "title": "Starfield BA2 Manažér a Kompresor (Cross-Platform)",
        "btn_load": "📂 Otvoriť BA2",
        "btn_back": "⬅ Späť / Hore",
        "lbl_no_file": "Žiadny archív nie je vybraný",
        "drop_zone_text": "📥 Dropni .ba2 sem",
        "compress_panel": " Nastavenia kompresorového balenia (Archive2 štýl) ",
        "lbl_source": "Zdrojový priečinok (Source):",
        "btn_browse": "Prehľadávať...",
        "lbl_dest": "Výstupný BA2 (Destination):",
        "btn_save_as": "Uložiť ako...",
        "chk_root": "Použiť root folder",
        "lbl_method": "Metóda:",
        "btn_compress": "📦 Vytvoriť / Zabaliť BA2",
        "col_structure": "Vnútorná štruktúra / Cesta k súboru",
        "col_size": "Veľkość (bajtov)",
        "col_offset": "Offset v archíve",
        "btn_extract_all": "Exportovať všetko",
        "btn_extract_selected": "Exportovať vybrané",
        "lbl_drop_hint": "💡 Tip: Pre podporu Drag & Drop nainštaluj 'tkinterdnd2' cez pip.",
        
        "err_invalid_magic": "Neplatný BA2 formát (chýba BTDX hlavička).",
        "err_parse": "Chyba pri parsovaní BA2: {}",
        "err_no_source_files": "Zdrojový priečinok neobsahuje žiadne súbory na zabalenie!",
        "err_select_source": "Prosím, vyber platný zdrojový priečinok!",
        "err_select_output": "Prosím, zadaj cestu a názov pre výstupný BA2 súbor!",
        "msg_compressed": "Archív bol úspešne vytvorený:\n{}",
        "msg_loaded": "Načítaných {} súborov (Detekovaný typ: {}).",
        "warn_open_first": "Najskôr otvor BA2 archív!",
        "warn_no_selection": "Nemáš vybrané žiadne súbory na export!",
        "msg_exported": "Exportovaných {} súborov.",
        "msg_exported_all": "Všetky súbory exportované."
    }
}

class StarfieldBA2Manager:
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.files = []
        self.archive_type = "General"

    @staticmethod
    def is_valid_path_string(s):
        """Overí, či reťazec vyzerá ako normálna cesta k súboru a nie je to binárny garbage."""
        if not s or len(s) > 512:
            return False
        bad_chars_count = sum(1 for ch in s if ord(ch) < 32 or (127 <= ord(ch) < 160) or ch in '§©®™¶†‡•ƒ')
        if bad_chars_count > 2 or ('\ufffd' in s):
            return False
        return True

    @staticmethod
    def sanitize_internal_path(raw_name, index, ext):
        """Univerzálne ošetrenie názvov pre Windows a Linux."""
        if not raw_name or not isinstance(raw_name, str):
            return f"file_{index:08X}.{ext}" if ext else f"file_{index:08X}"
        
        cleaned = "".join(ch for ch in raw_name if ord(ch) >= 32 or ch in ('\t', '\n', '\r'))
        cleaned = cleaned.strip().strip("\x00")
        
        if not cleaned:
            return f"file_{index:08X}.{ext}" if ext else f"file_{index:08X}"

        cleaned = cleaned.replace("\\", "/")
        parts = [p.strip() for p in cleaned.split("/") if p.strip()]
        if not parts:
            return f"file_{index:08X}.{ext}" if ext else f"file_{index:08X}"
            
        windows_reserved = {
            "con", "prn", "aux", "nul", 
            "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
            "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"
        }

        safe_parts = []
        for part in parts:
            sanitized_chars = []
            for ch in part:
                code = ord(ch)
                if ch in '<>:"\\|?*`' or code < 32:
                    sanitized_chars.append('_')
                else:
                    sanitized_chars.append(ch)
            part = "".join(sanitized_chars).strip(". ")

            if not part:
                part = "unnamed"

            base_name, file_ext = os.path.splitext(part)
            if base_name.lower() in windows_reserved:
                base_name = f"_{base_name}_"
                part = base_name + file_ext

            if len(part) > 240:
                if not file_ext and ext:
                    file_ext = f".{ext}"
                part = base_name[: 230 - len(file_ext)] + file_ext

            safe_parts.append(part)
            
        final_path = "/".join(safe_parts)
        if len(final_path) > 850:
            ext_part = f".{ext}" if ext else ""
            final_path = f"long_path_file_{index:08X}{ext_part}"
            
        return final_path

    def parse(self, t):
        try:
            file_size = os.path.getsize(self.filepath)
            with open(self.filepath, "rb") as f:
                magic = f.read(4)
                if magic != b'BTDX':
                    raise ValueError(t["err_invalid_magic"])
                
                version, = struct.unpack("<I", f.read(4))
                archive_type_bytes = f.read(4)
                
                if archive_type_bytes == b'DX10':
                    self.archive_type = "Texture (DX10)"
                else:
                    self.archive_type = "General"

                file_count, = struct.unpack("<I", f.read(4))
                name_offset, = struct.unpack("<Q", f.read(8))

                logger.debug(f"BA2 Parse: version={version}, type={self.archive_type}, count={file_count}, name_offset={name_offset}")

                file_headers = []
                for i in range(file_count):
                    name_hash, = struct.unpack("<I", f.read(4))
                    ext = f.read(4).decode('ascii', errors='ignore').strip('\x00').strip().lower()
                    flags, = struct.unpack("<I", f.read(4))
                    offset, = struct.unpack("<I", f.read(4))
                    packed_size, = struct.unpack("<I", f.read(4))
                    unpacked_size, = struct.unpack("<I", f.read(4))
                    f.read(4)

                    fallback_name = f"file_{i:08X}.{ext}" if ext else f"file_{i:08X}"

                    file_headers.append({
                        "name": fallback_name,
                        "ext": ext,
                        "offset": offset,
                        "size": unpacked_size if unpacked_size > 0 else packed_size,
                        "packed_size": packed_size,
                        "has_real_name": False
                    })

                if 0 < name_offset < file_size:
                    try:
                        f.seek(name_offset)
                        for i, fh in enumerate(file_headers):
                            if f.tell() + 2 > file_size:
                                break
                            name_length, = struct.unpack("<H", f.read(2))
                            if 0 < name_length < 2048 and f.tell() + name_length <= file_size:
                                raw_bytes = f.read(name_length)
                                try:
                                    raw_name = raw_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    raw_name = raw_bytes.decode('latin1', errors='ignore')

                                if self.is_valid_path_string(raw_name):
                                    sanitized = self.sanitize_internal_path(raw_name, i, fh["ext"])
                                    if sanitized:
                                        fh["name"] = sanitized
                                        fh["has_real_name"] = True
                    except Exception as ex:
                        logger.warning(f"Chyba pri čítaní názvov z name_offset: {ex}")

                seen_names = {}
                for fh in file_headers:
                    n = fh["name"]
                    if n in seen_names:
                        seen_names[n] += 1
                        base, ext_s = os.path.splitext(n)
                        fh["name"] = f"{base}_dup{seen_names[n]}{ext_s}"
                    else:
                        seen_names[n] = 0

                self.files = file_headers
        except Exception as e:
            raise Exception(t["err_parse"].format(e))

    @staticmethod
    def create_ba2(input_folder, output_filepath, use_root_folder, compression_mode, t):
        files_to_pack = []
        for root, dirs, filenames in os.walk(input_folder):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, input_folder).replace("\\", "/")
                files_to_pack.append((full_path, rel_path))

        file_count = len(files_to_pack)
        if file_count == 0:
            raise ValueError(t["err_no_source_files"])

        arc_type = b'GNRL' if compression_mode == "General" else b'DX10'

        with open(output_filepath, "wb") as f:
            f.write(b'BTDX')
            f.write(struct.pack("<I", 1))
            f.write(arc_type)
            f.write(struct.pack("<I", file_count))
            
            name_offset_pos = f.tell()
            f.write(struct.pack("<Q", 0))

            headers_size = 24 * file_count
            current_data_offset = f.tell() + headers_size

            header_entries = []
            file_payloads = []

            for full_path, rel_path in files_to_pack:
                if os.path.isdir(full_path):
                    continue
                with open(full_path, "rb") as sf:
                    data = sf.read()
                
                size = len(data)
                ext = os.path.splitext(rel_path)[1].lstrip(".").lower()[:3].encode('ascii', errors='ignore').ljust(4, b'\x00')
                name_hash = sum(ord(c) for c in rel_path.lower()) & 0xFFFFFFFF

                header_entries.append({
                    "hash": name_hash,
                    "ext": ext,
                    "offset": current_data_offset,
                    "size": size
                })
                file_payloads.append(data)
                current_data_offset += size

            file_count = len(header_entries)
            f.seek(4)
            f.write(struct.pack("<I", 1))
            f.write(arc_type)
            f.write(struct.pack("<I", file_count))
            f.seek(name_offset_pos)
            f.write(struct.pack("<Q", 0))

            headers_size = 24 * file_count
            current_data_offset = 24 + headers_size

            for i, h in enumerate(header_entries):
                h["offset"] = current_data_offset
                current_data_offset += h["size"]

            f.seek(24)
            for h in header_entries:
                f.write(struct.pack("<I", h["hash"]))
                f.write(h["ext"][:4])
                f.write(struct.pack("<I", 0))
                f.write(struct.pack("<I", h["offset"]))
                f.write(struct.pack("<I", h["size"]))
                f.write(struct.pack("<I", h["size"]))
                f.write(struct.pack("<I", 0))

            name_table_offset = f.tell()
            for (_, rel_path), h in zip(files_to_pack, header_entries):
                encoded_name = rel_path.encode('utf-8', errors='ignore')
                f.write(struct.pack("<H", len(encoded_name)))
                f.write(encoded_name)

            f.seek(16)
            f.write(struct.pack("<Q", name_table_offset))

            for h, data in zip(header_entries, file_payloads):
                f.seek(h["offset"])
                f.write(data)

BaseClass = TkinterDnD.Tk if TKINTERDND_AVAILABLE else tk.Tk

class BA2ManagerApp(BaseClass):
    def __init__(self):
        super().__init__()
        self.root = self
        self.current_lang = "Slovenčina"

        self.init_ui()
        self.update_texts()
        self.setup_dnd()

    def t(self):
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["English"])

    def init_ui(self):
        self.root.title("Starfield BA2 Manažér a Kompresor (Cross-Platform)")
        self.root.geometry("1150x860")
        self.root.minsize(1150, 860)
        self.root.resizable(False, False)

        top_frame = ttk.Frame(self.root, padding=5)
        top_frame.pack(fill=tk.X)

        self.btn_load = ttk.Button(top_frame, command=self.load_ba2)
        self.btn_load.pack(side=tk.LEFT, padx=2)

        self.lbl_drop_zone = ttk.Label(top_frame, relief="groove", padding=5)
        self.lbl_drop_zone.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        self.btn_back = ttk.Button(top_frame, command=self.go_back, state=tk.DISABLED)
        self.btn_back.pack(side=tk.LEFT, padx=2)

        self.lbl_file = ttk.Label(top_frame)
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        self.lbl_drop_info = ttk.Label(self.root, font=("Arial", 9, "italic"), padding=(10, 2))
        self.lbl_drop_info.pack(fill=tk.X)

        compress_panel = ttk.LabelFrame(self.root, padding=10)
        compress_panel.pack(fill=tk.X, padx=10, pady=5)
        self.compress_panel = compress_panel

        src_frame = ttk.Frame(compress_panel)
        src_frame.pack(fill=tk.X, pady=2)
        self.lbl_source_text = ttk.Label(src_frame, width=24)
        self.lbl_source_text.pack(side=tk.LEFT)
        self.txt_source = ttk.Entry(src_frame)
        self.txt_source.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.btn_browse_src = ttk.Button(src_frame, command=self.browse_source)
        self.btn_browse_src.pack(side=tk.RIGHT)

        out_frame = ttk.Frame(compress_panel)
        out_frame.pack(fill=tk.X, pady=5)
        self.lbl_dest_text = ttk.Label(out_frame, width=24)
        self.lbl_dest_text.pack(side=tk.LEFT)
        self.txt_output = ttk.Entry(out_frame)
        self.txt_output.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.btn_browse_out = ttk.Button(out_frame, command=self.browse_output)
        self.btn_browse_out.pack(side=tk.RIGHT)

        options_frame = ttk.Frame(compress_panel)
        options_frame.pack(fill=tk.X, pady=5)

        self.use_root_var = tk.BooleanVar(value=True)
        self.chk_root = ttk.Checkbutton(options_frame, variable=self.use_root_var)
        self.chk_root.pack(side=tk.LEFT)

        self.lbl_method_text = ttk.Label(options_frame)
        self.lbl_method_text.pack(side=tk.LEFT, padx=(15, 5))
        self.compression_var = tk.StringVar(value="General")
        self.combo_compression = ttk.Combobox(options_frame, textvariable=self.compression_var, values=["General", "Texture (DX10)"], state="readonly", width=16)
        self.combo_compression.pack(side=tk.LEFT)
        self.combo_compression.configure(exportselection=False)

        self.btn_compress = ttk.Button(options_frame, command=self.execute_compression)
        self.btn_compress.pack(side=tk.RIGHT)

        center_frame = ttk.Frame(self.root, padding=5)
        center_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.tree = ttk.Treeview(center_frame, columns=("path", "size", "offset"), show="headings", selectmode="extended")
        self.tree.heading("path", text="Vnútorná štruktúra / Cesta k súboru")
        self.tree.heading("size", text="Veľkość (bajtov)")
        self.tree.heading("offset", text="Offset v archíve")
        
        self.tree.column("path", width=700, anchor=tk.W)
        self.tree.column("size", width=180, anchor=tk.E)
        self.tree.column("offset", width=180, anchor=tk.E)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(center_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X)

        self.btn_extract_all = ttk.Button(bottom_frame, command=self.extract_all)
        self.btn_extract_all.pack(side=tk.LEFT)

        self.btn_extract = ttk.Button(bottom_frame, command=self.extract_selected)
        self.btn_extract.pack(side=tk.RIGHT)

        self.current_manager = None

    def setup_dnd(self):
        if not TKINTERDND_AVAILABLE:
            return

        def _register(widget, name):
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', self.handle_dnd_drop)
                return True
            except Exception:
                return False

        def _register_recursive(widget, path_name):
            ok = _register(widget, path_name)
            count = 1 if ok else 0
            for child in widget.winfo_children():
                count += _register_recursive(child, f"{path_name} > {child.winfo_class()}")
            return count

        _register_recursive(self, "root")

    def handle_dnd_drop(self, event):
        self.process_dropped_paths(event.data)

    def process_dropped_paths(self, raw_data):
        try:
            paths = self.tk.splitlist(raw_data)
        except Exception:
            paths = [raw_data]

        cleaned_paths = []
        for item in paths:
            item = item.strip(' \n\r')
            if item.startswith('file://'):
                item = item[7:]
            import urllib.parse
            item = urllib.parse.unquote(item)
            if os.path.exists(item):
                cleaned_paths.append(item)

        for path in cleaned_paths:
            if path.lower().endswith('.ba2'):
                self.load_ba2_from_path(path)
                return

    def update_texts(self):
        t = self.t()
        self.root.title(t["title"])
        self.btn_load.config(text=t["btn_load"])
        self.lbl_drop_zone.config(text=t["drop_zone_text"])
        self.btn_back.config(text=t["btn_back"])
        if not self.current_manager:
            self.lbl_file.config(text=t["lbl_no_file"])
        self.lbl_drop_info.config(text=t["lbl_drop_hint"])
        self.compress_panel.config(text=t["compress_panel"])
        self.lbl_source_text.config(text=t["lbl_source"])
        self.btn_browse_src.config(text=t["btn_browse"])
        self.lbl_dest_text.config(text=t["lbl_dest"])
        self.btn_browse_out.config(text=t["btn_save_as"])
        self.chk_root.config(text=t["chk_root"])
        self.lbl_method_text.config(text=t["lbl_method"])
        self.btn_compress.config(text=t["btn_compress"])
        self.tree.heading("path", text=t["col_structure"])
        self.tree.heading("size", text=t["col_size"])
        self.tree.heading("offset", text=t["col_offset"])
        self.btn_extract_all.config(text=t["btn_extract_all"])
        self.btn_extract.config(text=t["btn_extract_selected"])

    def browse_source(self):
        folder = filedialog.askdirectory(title="Vybrať zdrojový priečinok")
        if folder:
            self.txt_source.delete(0, tk.END)
            self.txt_source.insert(0, folder)

    def browse_output(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".ba2", filetypes=[("Starfield BA2 archív", "*.ba2")])
        if filepath:
            self.txt_output.delete(0, tk.END)
            self.txt_output.insert(0, filepath)

    def execute_compression(self):
        t = self.t()
        input_folder = self.txt_source.get().strip()
        output_filepath = self.txt_output.get().strip()
        if not input_folder or not os.path.exists(input_folder):
            messagebox.showerror("Chyba", t["err_select_source"])
            return
        if not output_filepath:
            messagebox.showerror("Chyba", t["err_select_output"])
            return
        try:
            use_root = self.use_root_var.get()
            comp_mode = self.compression_var.get()
            StarfieldBA2Manager.create_ba2(input_folder, output_filepath, use_root, comp_mode, t)
            messagebox.showinfo("Hotovo", t["msg_compressed"].format(output_filepath))
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def load_ba2(self):
        file_path = filedialog.askopenfilename(filetypes=[("Starfield BA2 archívy", "*.ba2"), ("Všetky súbory", "*.*")])
        if file_path:
            self.load_ba2_from_path(file_path)

    def load_ba2_from_path(self, file_path):
        t = self.t()
        if not os.path.exists(file_path):
            messagebox.showerror("Chyba", f"Súbor nebol nájdený:\n{file_path}")
            return
        try:
            manager = StarfieldBA2Manager(file_path)
            manager.parse(t)
            self.current_manager = manager
            self.lbl_file.config(text=file_path)
            if self.current_manager.archive_type in ["General", "Texture (DX10)"]:
                self.compression_var.set(self.current_manager.archive_type)
            self.load_tree_data()
            messagebox.showinfo("Úspech", t["msg_loaded"].format(len(self.current_manager.files), self.current_manager.archive_type))
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def load_tree_data(self):
        self.tree.delete(*self.tree.get_children())
        self.btn_back.config(state=tk.DISABLED)
        for idx, file_info in enumerate(self.current_manager.files):
            self.tree.insert("", tk.END, values=(file_info["name"], file_info["size"], file_info["offset"]), iid=str(idx))

    def go_back(self):
        pass

    def _extract_indices(self, indices, output_dir):
        t = self.t()
        if not indices:
            messagebox.showwarning("Pozor", t["warn_no_selection"])
            return 0
        with open(self.current_manager.filepath, "rb") as f:
            count = 0
            for idx_str in indices:
                try:
                    idx = int(idx_str)
                except ValueError:
                    continue
                if idx < 0 or idx >= len(self.current_manager.files):
                    continue
                file_info = self.current_manager.files[idx]
                rel_path = file_info["name"]
                
                rel_path = os.path.normpath(rel_path).lstrip(os.sep).lstrip("/")
                if not rel_path:
                    rel_path = f"extracted_file_{idx:08X}"

                out_filepath = os.path.join(output_dir, rel_path)
                
                if len(out_filepath) > 4000:
                    out_filepath = os.path.join(output_dir, f"safe_extract_{idx:08X}")

                if file_info["size"] == 0:
                    os.makedirs(out_filepath, exist_ok=True)
                    continue

                f.seek(file_info["offset"])
                data = f.read(file_info["size"])
                
                os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
                with open(out_filepath, "wb") as of:
                    of.write(data)
                count += 1
        return count

    def extract_selected(self):
        t = self.t()
        if not self.current_manager:
            messagebox.showwarning("Pozor", t["warn_open_first"])
            return
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Pozor", t["warn_no_selection"])
            return
        file_indices = list(selected_items)
        output_dir = filedialog.askdirectory(title="Vybrať priečinok pre export")
        if not output_dir:
            return
        try:
            count = self._extract_indices(file_indices, output_dir)
            messagebox.showinfo("Hotovo", t["msg_exported"].format(count))
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def extract_all(self):
        t = self.t()
        if not self.current_manager:
            messagebox.showwarning("Pozor", t["warn_open_first"])
            return
        output_dir = filedialog.askdirectory(title="Vybrať priečinok pre export všetkých súborov")
        if not output_dir:
            return
        try:
            all_indices = [str(i) for i in range(len(self.current_manager.files))]
            self._extract_indices(all_indices, output_dir)
            messagebox.showinfo("Hotovo", t["msg_exported_all"])
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

if __name__ == "__main__":
    app = BA2ManagerApp()
    app.mainloop()
