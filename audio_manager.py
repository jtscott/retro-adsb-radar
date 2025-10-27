import vlc

class AudioManager:
    """Manages ATC audio stream playback using a single, persistent VLC instance."""
    def __init__(self, stream_url: str = None):
        self.stream_url = stream_url
        self.player = None
        self.instance = None
        self.initialised = False

    def initialise(self) -> bool:
        """Initialise VLC instance and load stream if URL provided"""
        if not self.stream_url or self.initialised:
            return False

        try:
            self.instance = vlc.Instance('--no-xlib')
            self.player = self.instance.media_player_new()
            media = self.instance.media_new(self.stream_url)
            media.add_option(':network-caching=1000')
            self.player.set_media(media)
            self.initialised = True
            print("✅ Audio manager initialised successfully")
            return True
        except Exception as e:
            print(f"❌ Error initialising audio. Is VLC installed? Details: {e}")
            self.player = None
            self.instance = None
            return False

    def toggle(self):
        """Toggles the audio stream on or off."""
        if not self.player:
            return

        if self.player.is_playing():
            self.player.stop()
            print("✅ Audio stream stopped")
        else:
            self.player.play()
            print("✅ Audio stream started")

    def is_playing(self) -> bool:
        """Returns True if the audio stream is currently playing."""
        if not self.player:
            return False
        return self.player.is_playing()

    def shutdown(self):
        """Stops playback and releases VLC resources cleanly."""
        if self.player:
            self.player.stop()
        if self.instance:
            self.instance.release()
        self.player = None
        self.instance = None
        print("✅ Audio shut down cleanly")

