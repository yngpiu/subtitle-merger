# processor.py
import subprocess
import sys
import os
import re
import time

def escape_path_for_ffmpeg_filter(path: str) -> str:
    if sys.platform == "win32":
        path = path.replace('\\', '\\\\')
        path = path.replace(':', '\\:')
    return path

def get_video_duration(video_path: str, ffmpeg_executable: str) -> tuple[float, str]:
    command = [ffmpeg_executable, "-i", video_path]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        output = result.stderr
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})", output)
        if match:
            hours, minutes, seconds, hundredths = map(int, match.groups())
            total_seconds = float(hours * 3600 + minutes * 60 + seconds + hundredths / 100)
            total_duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            return total_seconds, total_duration_str
    except Exception:
        pass
    return 0.0, "00:00:00"

def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_int = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds_int:02}"

def run_processing_logic(params, status_callback, pause_event, cancel_requested_getter):
    process = None
    output_path = params.get('output_path', '')
    try:
        try:
            logo_width = int(params['logo_width'])
            margin_top = int(params['margin_top'])
            margin_right = int(params['margin_right'])
            bitrate_val = int(params['bitrate'])
            if not all(x > 0 for x in [logo_width, bitrate_val]): raise ValueError("Logo Width và Bitrate phải là số dương.")
            if not all(x >= 0 for x in [margin_top, margin_right]): raise ValueError("Margin Top và Margin Right không được là số âm.")
        except (ValueError, KeyError):
            raise ValueError("Các giá trị tùy chọn phải là số nguyên hợp lệ.")

        ffmpeg_executable = get_ffmpeg_path()
        if not os.path.exists(ffmpeg_executable):
            raise FileNotFoundError(f"Không tìm thấy {ffmpeg_executable}.")

        video_path = params['video_path']
        logo_path = params['logo_path']
        subtitle_path = params['subtitle_path']
        codec = params['codec']

        status_callback("1/4: Đang lấy thông tin video...")
        total_duration_seconds, total_duration_str = get_video_duration(video_path, ffmpeg_executable)
        if total_duration_seconds <= 0:
            raise ValueError("Không thể xác định thời lượng video.")
        status_callback(f"TIME_INFO|00:00:00|{total_duration_str}")

        status_callback("2/4: Đang xây dựng lệnh FFmpeg...")
        time.sleep(0.1)

        escaped_subtitle_path = escape_path_for_ffmpeg_filter(subtitle_path)
        filter_complex_string = (f"[1:v]scale={logo_width}:-1[logo];[0:v][logo]overlay=W-w-{margin_right}:{margin_top}[video_with_logo];[video_with_logo]subtitles='{escaped_subtitle_path}'")
        command = [ffmpeg_executable, '-y', '-i', video_path, '-i', logo_path, '-filter_complex', filter_complex_string, '-c:v', codec, '-b:v', f'{bitrate_val}k', '-maxrate', f'{bitrate_val}k', '-bufsize', f'{bitrate_val * 2}k', output_path]

        status_callback("3/4: Bắt đầu xử lý...")

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        for line in process.stdout:
            pause_event.wait()
            if cancel_requested_getter():
                status_callback("Đang hủy bỏ...")
                process.terminate()
                process.wait(timeout=5)
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                        status_callback("Đã hủy bỏ và xóa file output.")
                    else:
                        status_callback("Đã hủy bỏ bởi người dùng.")
                except OSError as e:
                    status_callback(f"Đã hủy, nhưng không thể xóa file: {e}")
                return
            time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
            if time_match:
                hours, minutes, seconds, hundredths = map(int, time_match.groups())
                current_time_seconds = float(hours * 3600 + minutes * 60 + seconds + hundredths / 100)
                percentage = int((current_time_seconds / total_duration_seconds) * 100)
                current_time_str = format_time(current_time_seconds)
                status_callback(f"PROGRESS|{percentage}")
                status_callback(f"TIME_INFO|{current_time_str}|{total_duration_str}")
        process.wait()
        if process.returncode == 0:
            # --- THAY ĐỔI: Bỏ icon ---
            status_callback(f"4/4: Hoàn thành! Video đã được lưu tại {output_path}")
        elif not cancel_requested_getter():
            raise RuntimeError(f"FFmpeg thoát với mã lỗi {process.returncode}.")
    except Exception as e:
        # --- THAY ĐỔI: Bỏ icon ---
        status_callback(f"Lỗi: {e}")
    finally:
        if process and process.poll() is None:
            process.terminate()

def get_ffmpeg_path() -> str:
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, "ffmpeg.exe")

