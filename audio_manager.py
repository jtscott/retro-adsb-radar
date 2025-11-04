import threading
import time


class AudioManager:
    """Manages ATC audio stream playback using a single, persistent VLC instance."""
    
    def __init__(self, stream_url: str = None):
        self.stream_url = stream_url
        self.player = None
        self.instance = None
        self.initialised = False
        self._playback_thread = None
        self._stop_thread = threading.Event()
        self._vlc_module = None
        
    def initialise(self) -> bool:
        """
        Initialises the VLC instance and loads the stream.
        The 'vlc' module is imported here to make it an optional dependency.
        """
        if not self.stream_url or self.initialised:
            return False
        
        try:
            import vlc
            self._vlc_module = vlc
            
            # Create VLC instance with verbose logging for debugging
            self.instance = vlc.Instance('--verbose=1')
            self.player = self.instance.media_player_new()
            
            # Create and configure media
            media = self.instance.media_new(self.stream_url)
            media.add_option(':network-caching=5000')  # 5 second buffer
            media.add_option(':file-caching=5000')
            media.add_option(':live-caching=5000')
            media.add_option(':clock-jitter=0')
            media.add_option(':clock-synchro=0')
            
            self.player.set_media(media)
            
            # Attach event handlers for monitoring
            events = self.player.event_manager()
            events.event_attach(vlc.EventType.MediaPlayerBuffering, self._handle_buffering)
            events.event_attach(vlc.EventType.MediaPlayerPlaying, self._handle_playing)
            events.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._handle_error)
            events.event_attach(vlc.EventType.MediaPlayerStopped, self._handle_stopped)
            
            self.initialised = True
            print("✅ Audio manager initialised successfully")
            return True
            
        except ModuleNotFoundError:
            print("❌ Error: 'python-vlc' not found. Please install it to use the audio feature.")
            return False
        except Exception as e:
            print(f"❌ Error initialising audio. Is the VLC application installed? Details: {e}")
            self.player = None
            self.instance = None
            return False
    
    def _playback_loop(self):
        """Internal thread to keep VLC event loop alive and monitor state."""
        while not self._stop_thread.is_set():
            if self.player:
                state = self.player.get_state()
                
                # Check for error or ended states
                if state == self._vlc_module.State.Error:
                    print("❌ VLC playback error detected")
                    break
                elif state == self._vlc_module.State.Ended:
                    print("⚠️ Stream ended")
                    break
            
            # Small sleep to avoid busy waiting
            time.sleep(0.1)
    
    def toggle(self):
        """Toggles the audio stream on or off."""
        if not self.player:
            return
        
        if self.player.is_playing():
            self.stop()
        else:
            self.play()
    
    def play(self):
        """Starts audio playback in a background thread."""
        if not self.player:
            return
        
        # Start playback
        self.player.play()
        
        # Start monitoring thread if not already running
        if not self._playback_thread or not self._playback_thread.is_alive():
            self._stop_thread.clear()
            self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self._playback_thread.start()
        
        print("✅ Audio stream started")
    
    def stop(self):
        """Stops audio playback and monitoring thread."""
        if self.player:
            self.player.stop()
        
        self._stop_thread.set()
        
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=1.0)
        
        print("✅ Audio stream stopped")
    
    def is_playing(self) -> bool:
        """Returns True if the audio stream is currently playing."""
        if not self.player:
            return False
        return self.player.is_playing()
    
    def shutdown(self):
        """Stops playback and releases VLC resources cleanly."""
        self.stop()
        
        if self.player:
            self.player.release()
        
        if self.instance:
            self.instance.release()
        
        self.player = None
        self.instance = None
        self.initialised = False
        
        print("✅ Audio shut down cleanly")
    
    # ========== VLC Event Handlers ==========
    
    def _handle_buffering(self, event):
        """Called when VLC is buffering."""
        print(f"🔄 Buffering: {event.u.new_cache}%")
    
    def _handle_playing(self, event):
        """Called when VLC starts playing."""
        print("▶️  Playback started")
    
    def _handle_error(self, event):
        """Called when VLC encounters an error."""
        print("❌ VLC playback error encountered")
    
    def _handle_stopped(self, event):
        """Called when VLC stops."""
        print("⏹️  Playback stopped")
