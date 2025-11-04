import subprocess
import threading
import time


class AudioManager:
    """
    Manages ATC audio stream playback using an external VLC subprocess.
    Runs VLC with high buffer settings and controls playback lifecycle.
    """
    def __init__(self, stream_url: str = None):
        self.stream_url = stream_url
        self.process = None
        self.initialised = False
        self._poll_thread = None
        self._stop_poll = threading.Event()
    
    def initialise(self) -> bool:
        if not self.stream_url:
            print("❌ No stream URL configured")
            return False
        self.initialised = True
        print("✅ Audio manager initialised")
        return True

    def _poll_process(self):
        while not self._stop_poll.is_set():
            if self.process:
                retcode = self.process.poll()
                if retcode is not None:
                    print(f"❌ VLC process exited with code {retcode}")
                    self.process = None
                    self._stop_poll.set()
                    break
            time.sleep(0.5)

    def play(self):
        if not self.initialised:
            return
        if self.is_playing():
            print("ℹ️ Already playing")
            return
        try:
            self.process = subprocess.Popen([
                'cvlc',  # Use cvlc for no GUI
                '--quiet',
                '--network-caching=10000',  # 10 sec buffer for stability
                self.stream_url
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._stop_poll.clear()
            self._poll_thread = threading.Thread(target=self._poll_process, daemon=True)
            self._poll_thread.start()
            print("▶️  Audio stream started")
        except FileNotFoundError:
            print("❌ VLC not found. Make sure VLC is installed and 'cvlc' is in PATH")

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self._stop_poll.set()
            if self._poll_thread:
                self._poll_thread.join(timeout=1)
            print("⏹️  Audio stream stopped")

    def toggle(self):
        if self.is_playing():
            self.stop()
        else:
            self.play()

    def is_playing(self):
        return self.process is not None and self.process.poll() is None

    def shutdown(self):
        self.stop()
        self.initialised = False
        print("✅ Audio manager shut down cleanly")
