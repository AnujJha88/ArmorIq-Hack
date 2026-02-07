"""
Policy Hot-Reload
=================
File watcher for automatic policy hot-reloading.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("TIRS.HotReload")

# Try to import watchdog, fallback to polling if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed - using polling fallback for hot-reload")


class PolicyWatcher:
    """
    Watches policy config files for changes and triggers reload.
    
    Uses watchdog if available, otherwise falls back to polling.
    """

    def __init__(
        self,
        watch_path: Optional[Path] = None,
        on_change: Optional[Callable] = None,
        debounce_seconds: float = 1.0
    ):
        """
        Initialize policy watcher.
        
        Args:
            watch_path: Directory to watch. Defaults to hr_delegate/data/.
            on_change: Callback function when changes detected.
            debounce_seconds: Minimum time between reload triggers.
        """
        if watch_path is None:
            self.watch_path = Path(__file__).parent.parent / "data"
        else:
            self.watch_path = Path(watch_path)
        
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        self._last_trigger = 0.0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        if WATCHDOG_AVAILABLE:
            self._observer: Optional[Observer] = None
        else:
            self._file_mtimes: dict = {}

    def _should_trigger(self) -> bool:
        """Check if enough time has passed since last trigger."""
        now = time.time()
        if now - self._last_trigger >= self.debounce_seconds:
            self._last_trigger = now
            return True
        return False

    def _handle_change(self, path: str) -> None:
        """Handle file change event."""
        if not self._should_trigger():
            return
        
        logger.info(f"Policy file changed: {path}")
        
        if self.on_change:
            try:
                self.on_change()
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

    def start_watching(self) -> None:
        """Start watching for file changes."""
        if self._running:
            logger.warning("Watcher already running")
            return
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()
        
        logger.info(f"Started watching: {self.watch_path}")

    def _start_watchdog(self) -> None:
        """Start watchdog observer."""
        class PolicyHandler(FileSystemEventHandler):
            def __init__(handler_self, watcher):
                handler_self.watcher = watcher
            
            def on_modified(handler_self, event):
                if isinstance(event, FileModifiedEvent):
                    if event.src_path.endswith(".json"):
                        handler_self.watcher._handle_change(event.src_path)
        
        self._observer = Observer()
        self._observer.schedule(
            PolicyHandler(self),
            str(self.watch_path),
            recursive=True
        )
        self._observer.start()

    def _start_polling(self) -> None:
        """Start polling fallback."""
        # Initialize mtimes
        self._update_mtimes()
        
        def poll_loop():
            while self._running:
                time.sleep(2)  # Check every 2 seconds
                if self._check_for_changes():
                    self._handle_change("policies_config.json")
        
        self._thread = threading.Thread(target=poll_loop, daemon=True)
        self._thread.start()

    def _update_mtimes(self) -> None:
        """Update stored file modification times."""
        self._file_mtimes.clear()
        for path in self.watch_path.glob("**/*.json"):
            try:
                self._file_mtimes[str(path)] = path.stat().st_mtime
            except Exception:
                pass

    def _check_for_changes(self) -> bool:
        """Check if any files have changed."""
        for path in self.watch_path.glob("**/*.json"):
            try:
                path_str = str(path)
                mtime = path.stat().st_mtime
                
                if path_str not in self._file_mtimes:
                    self._file_mtimes[path_str] = mtime
                    return True
                
                if mtime > self._file_mtimes[path_str]:
                    self._file_mtimes[path_str] = mtime
                    return True
            except Exception:
                pass
        
        return False

    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        self._running = False
        
        if WATCHDOG_AVAILABLE and self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        logger.info("Stopped watching")

    def reload_now(self) -> None:
        """Manually trigger reload."""
        logger.info("Manual reload triggered")
        if self.on_change:
            self.on_change()


# Singleton watcher
_watcher: Optional[PolicyWatcher] = None


def get_watcher(on_change: Optional[Callable] = None) -> PolicyWatcher:
    """Get the singleton policy watcher."""
    global _watcher
    if _watcher is None:
        from .policy_registry import get_registry
        registry = get_registry()
        _watcher = PolicyWatcher(on_change=on_change or registry.reload_from_file)
    return _watcher
