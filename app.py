# app.py
import customtkinter as ctk
from tkinter import filedialog
import threading
import json
import os
import subprocess
import datetime
import queue
from processor import run_processing_logic


# ... (Hàm get_settings_path và biến SETTINGS_FILE giữ nguyên) ...
def get_settings_path():
    app_data_path = os.path.join(os.getenv('APPDATA'), "SubtitleMerger")
    os.makedirs(app_data_path, exist_ok=True)
    return os.path.join(app_data_path, "settings.json")


SETTINGS_FILE = get_settings_path()


class VideoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ... (Phần cấu hình cửa sổ và biến điều khiển giữ nguyên) ...
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Subtitle Merger")
        self.geometry("600x600")
        self.resizable(False, False)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(9, weight=1)
        self.processing_thread = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancel_requested = False
        self.is_paused = False
        self.log_queue = queue.Queue()

        self.create_widgets()
        self.load_settings()
        self._on_codec_select(self.options['codec'].get(), initial_load=True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._process_log_queue()

    def _process_log_queue(self):
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get_nowait()
                self._handle_status_update(message)
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_log_queue)

    def _handle_status_update(self, message):
        if message.startswith("PROGRESS|"):
            try:
                percentage = int(message.split("|")[1])
                self.progress_bar.set(percentage / 100)
            except (ValueError, IndexError):
                pass
        elif message.startswith("TIME_INFO|"):
            try:
                current_time_str, total_duration_str = message.split("|")[1:3]
                self.time_info_label.configure(text=f"{current_time_str} / {total_duration_str}")
            except (ValueError, IndexError):
                pass
        else:
            level = "INFO"
            # --- THAY ĐỔI: Kiểm tra log không còn icon ---
            if "Hoàn thành!" in message:
                level = "SUCCESS"
            elif "Lỗi:" in message:
                level = "ERROR"
            elif "Cảnh báo:" in message:
                level = "WARNING"
            elif "Đã hủy bỏ" in message:
                level = "WARNING"
            self._log_message(message, level)

    def status_callback(self, message):
        self.log_queue.put(message)

    def _toggle_pause_resume(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_event.clear()
            # --- THAY ĐỔI: Bỏ icon ---
            self.pause_resume_button.configure(text="Resume")
            self._log_message("Quá trình xử lý đã tạm dừng.", "WARNING")
        else:
            self.pause_event.set()
            # --- THAY ĐỔI: Bỏ icon ---
            self.pause_resume_button.configure(text="Pause")
            self._log_message("Quá trình xử lý được tiếp tục.", "INFO")

    def _cancel_processing(self):
        self.cancel_requested = True
        if self.is_paused: self.pause_event.set()
        self.cancel_button.configure(state="disabled", text="Đang hủy...")

    def _reset_ui_to_idle(self):
        self.pause_resume_button.grid_remove()
        self.cancel_button.grid_remove()
        self.process_button.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.process_button.configure(state="normal", text="Bắt đầu Xử lý")
        log_content = self.log_textbox.get("1.0", "end-1c")
        # --- THAY ĐỔI: Kiểm tra log không còn icon ---
        if "Hoàn thành!" in log_content:
            self.post_process_frame.grid()

    def _play_video(self):
        output_path = self.paths['output_path'].get()
        if output_path and os.path.exists(output_path):
            try:
                os.startfile(output_path)
            except Exception as e:
                self._log_message(f"Không thể mở video: {e}", "ERROR")

    def _open_output_folder(self):
        output_path = self.paths['output_path'].get()
        if output_path and os.path.exists(output_path):
            try:
                subprocess.run(['explorer', '/select,', os.path.normpath(output_path)])
            except Exception as e:
                self._log_message(f"Không thể mở thư mục: {e}", "ERROR")

    def _log_message(self, message: str, level: str = "INFO"):
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            full_message = f"[{timestamp}] [{level.upper()}] {message}\n"
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", full_message, level.upper())
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")
            self.update_idletasks()
        except Exception as e:
            print(f"Lỗi khi ghi log: {e}")

    def _validate_numeric_input(self, P):
        return P.isdigit() or P == ""

    def _on_codec_select(self, selected_value, initial_load=False):
        if not initial_load: self.options['codec'].set(selected_value)
        for value, button in self.codec_buttons.items(): button.configure(
            fg_color="black" if value == selected_value else "white",
            text_color="white" if value == selected_value else "black")

    def create_widgets(self):
        self.validation_cmd = self.register(self._validate_numeric_input)
        self.paths = {'video_path': ctk.StringVar(), 'logo_path': ctk.StringVar(), 'subtitle_path': ctk.StringVar(),
                      'output_path': ctk.StringVar()}
        self.create_file_input("Video:", 0, self.paths['video_path'])
        self.create_file_input("Logo:", 1, self.paths['logo_path'])
        self.create_file_input("Phụ đề:", 2, self.paths['subtitle_path'])
        self.create_file_input("Lưu tại:", 3, self.paths['output_path'], save=True)
        self.create_options_frame(4)
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, columnspan=3, padx=20, pady=(10, 5), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=2)
        self.action_frame.grid_columnconfigure((1, 2), weight=1)
        self.process_button = ctk.CTkButton(self.action_frame, text="Bắt đầu Xử lý",
                                            command=self.start_processing_thread, fg_color="black", text_color="white",
                                            hover_color="gray", border_width=1, border_color="black", corner_radius=0)
        self.process_button.grid(row=0, column=0, columnspan=3, sticky="ew")

        # --- THAY ĐỔI: Bỏ icon ---
        self.pause_resume_button = ctk.CTkButton(self.action_frame, text="Pause", command=self._toggle_pause_resume,
                                                 fg_color="white", text_color="black", hover_color="lightgray",
                                                 border_width=1, border_color="black", corner_radius=0)
        self.cancel_button = ctk.CTkButton(self.action_frame, text="Cancel", command=self._cancel_processing,
                                           fg_color="#D84646", text_color="white", hover_color="#B53A3A",
                                           border_width=1, border_color="black", corner_radius=0)

        self.post_process_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.post_process_frame.grid(row=6, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")
        self.post_process_frame.grid_columnconfigure((0, 1), weight=1)

        # --- THAY ĐỔI: Bỏ icon ---
        self.play_button = ctk.CTkButton(self.post_process_frame, text="Play Video", command=self._play_video,
                                         fg_color="white", text_color="black", hover_color="lightgray", border_width=1,
                                         border_color="black", corner_radius=0)
        self.play_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.open_folder_button = ctk.CTkButton(self.post_process_frame, text="Open Folder",
                                                command=self._open_output_folder, fg_color="white", text_color="black",
                                                hover_color="lightgray", border_width=1, border_color="black",
                                                corner_radius=0)
        self.open_folder_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        self.post_process_frame.grid_remove()

        self.progress_bar = ctk.CTkProgressBar(self, mode='determinate', fg_color="lightgray", progress_color="black",
                                               corner_radius=0)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=7, column=0, columnspan=3, padx=20, pady=(0, 5), sticky="ew")
        self.time_info_label = ctk.CTkLabel(self, text="00:00:00 / 00:00:00",
                                            font=ctk.CTkFont(size=12, family="Consolas"), text_color="black")
        self.time_info_label.grid(row=8, column=0, columnspan=3, padx=20, pady=0, sticky="ew")
        self.log_textbox = ctk.CTkTextbox(self, state="disabled", corner_radius=0, border_width=1, border_color="black",
                                          fg_color="white", text_color="black",
                                          font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=9, column=0, columnspan=3, padx=20, pady=(5, 10), sticky="nsew")
        self.log_textbox.tag_config("INFO", foreground="gray")
        self.log_textbox.tag_config("SUCCESS", foreground="green")
        self.log_textbox.tag_config("ERROR", foreground="red")
        self.log_textbox.tag_config("WARNING", foreground="#E69000")
        self._log_message("Ứng dụng đã sẵn sàng.", "INFO")

    def create_file_input(self, label_text, row, var, save=False):
        label = ctk.CTkLabel(self, text=label_text, width=80, anchor="w", text_color="black")
        label.grid(row=row, column=0, padx=(20, 5), pady=5, sticky="w")
        entry = ctk.CTkEntry(self, textvariable=var, state="disabled", border_width=1, border_color="black",
                             fg_color="white", text_color="black", corner_radius=0)
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        button = ctk.CTkButton(self, text="Chọn...", width=80, command=lambda: self.browse_file(var, save),
                               fg_color="white", text_color="black", hover_color="lightgray", border_width=1,
                               border_color="black", corner_radius=0)
        button.grid(row=row, column=2, padx=(5, 20), pady=5)

    def browse_file(self, var, save=False):
        filetypes = []
        if var == self.paths['video_path']:
            filetypes = [("Video files", "*.mp4")]
        elif var == self.paths['logo_path']:
            filetypes = [("PNG images", "*.png")]
        elif var == self.paths['subtitle_path']:
            filetypes = [("ASS subtitles", "*.ass")]
        elif var == self.paths['output_path']:
            filetypes = [("MP4 video", "*.mp4")]
        filename = filedialog.asksaveasfilename(defaultextension=".mp4",
                                                filetypes=filetypes) if save else filedialog.askopenfilename(
            filetypes=filetypes)
        if filename: var.set(filename)

    def create_options_frame(self, row):
        options_frame = ctk.CTkFrame(self, border_width=1, border_color="black", fg_color="white", corner_radius=0)
        options_frame.grid(row=row, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        options_frame.grid_columnconfigure((1, 3), weight=1)
        self.options = {'logo_width': ctk.StringVar(value="110"), 'margin_top': ctk.StringVar(value="10"),
                        'margin_right': ctk.StringVar(value="10"), 'bitrate': ctk.StringVar(value="3000"),
                        'codec': ctk.StringVar(value="libx264")}
        validate_args = {'validate': 'key', 'validatecommand': (self.register(self._validate_numeric_input), '%P')}
        ctk.CTkLabel(options_frame, text="Logo Width:", text_color="black").grid(row=0, column=0, padx=(10, 5), pady=5,
                                                                                 sticky="w")
        ctk.CTkEntry(options_frame, textvariable=self.options['logo_width'], **validate_args, border_width=1,
                     border_color="black", fg_color="white", text_color="black", corner_radius=0).grid(row=0, column=1,
                                                                                                       padx=5, pady=5,
                                                                                                       sticky="ew")
        ctk.CTkLabel(options_frame, text="Margin Top:", text_color="black").grid(row=0, column=2, padx=(10, 5), pady=5,
                                                                                 sticky="w")
        ctk.CTkEntry(options_frame, textvariable=self.options['margin_top'], **validate_args, border_width=1,
                     border_color="black", fg_color="white", text_color="black", corner_radius=0).grid(row=0, column=3,
                                                                                                       padx=(5, 10),
                                                                                                       pady=5,
                                                                                                       sticky="ew")
        ctk.CTkLabel(options_frame, text="Margin Right:", text_color="black").grid(row=1, column=0, padx=(10, 5),
                                                                                   pady=5, sticky="w")
        ctk.CTkEntry(options_frame, textvariable=self.options['margin_right'], **validate_args, border_width=1,
                     border_color="black", fg_color="white", text_color="black", corner_radius=0).grid(row=1, column=1,
                                                                                                       padx=5, pady=5,
                                                                                                       sticky="ew")
        ctk.CTkLabel(options_frame, text="Bitrate (kbps):", text_color="black").grid(row=1, column=2, padx=(10, 5),
                                                                                     pady=5, sticky="w")
        ctk.CTkEntry(options_frame, textvariable=self.options['bitrate'], **validate_args, border_width=1,
                     border_color="black", fg_color="white", text_color="black", corner_radius=0).grid(row=1, column=3,
                                                                                                       padx=(5, 10),
                                                                                                       pady=5,
                                                                                                       sticky="ew")
        ctk.CTkLabel(options_frame, text="Codec:", text_color="black").grid(row=2, column=0, padx=(10, 5), pady=10,
                                                                            sticky="w")
        codec_button_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        codec_button_frame.grid(row=2, column=1, columnspan=3, padx=(5, 10), pady=(5, 10), sticky="ew")
        codec_button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.codec_buttons = {}
        codecs_to_create = [{'text': "Software", 'value': "libx264"}, {'text': "AMD", 'value': "h264_amf"},
                            {'text': "Intel", 'value': "h264_qsv"}]
        for i, codec_info in enumerate(codecs_to_create):
            button = ctk.CTkButton(codec_button_frame, text=codec_info['text'],
                                   command=lambda v=codec_info['value']: self._on_codec_select(v), fg_color="white",
                                   text_color="black", border_width=1, border_color="black", hover_color="lightgray",
                                   corner_radius=0)
            button.grid(row=0, column=i, padx=0, pady=0, sticky="ew")
            self.codec_buttons[codec_info['value']] = button

    def start_processing_thread(self):
        self.log_textbox.configure(state="normal");
        self.log_textbox.delete("1.0", "end");
        self.log_textbox.configure(state="disabled")
        self.post_process_frame.grid_remove()
        self.cancel_requested = False
        self.is_paused = False
        self.pause_event.set()
        self.pause_resume_button.configure(text="Pause")
        self.cancel_button.configure(state="normal", text="Cancel")
        self.process_button.grid_remove()
        self.pause_resume_button.grid(row=0, column=0, columnspan=2, padx=(0, 5), sticky="ew")
        self.cancel_button.grid(row=0, column=2, columnspan=1, padx=(5, 0), sticky="ew")
        params = {key: var.get() for key, var in self.paths.items()}
        params.update({key: var.get() for key, var in self.options.items()})
        if not all([params['video_path'], params['logo_path'], params['subtitle_path'], params['output_path']]):
            self._log_message("Lỗi: Vui lòng điền đầy đủ các đường dẫn file.", "ERROR")
            self._reset_ui_to_idle()
            return
        self.progress_bar.set(0)
        self.time_info_label.configure(text="00:00:00 / 00:00:00")
        self.processing_thread = threading.Thread(target=run_processing_logic,
                                                  args=(params, self.status_callback, self.pause_event,
                                                        lambda: self.cancel_requested))
        self.processing_thread.start()
        self.check_thread()

    def check_thread(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.after(100, self.check_thread)
        else:
            self._reset_ui_to_idle()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    for key, value in settings.items():
                        if key in self.options: self.options[key].set(value)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Lỗi khi tải cài đặt: {e}")

    def save_settings(self):
        settings_to_save = {key: var.get() for key, var in self.options.items()}
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
        except IOError as e:
            print(f"Lỗi khi lưu cài đặt: {e}")

    def on_closing(self):
        self.cancel_requested = True
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1)
        self.save_settings()
        self.destroy()


if __name__ == "__main__":
    app = VideoApp()
    app.mainloop()

