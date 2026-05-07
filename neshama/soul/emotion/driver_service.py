# Soul Layer - Emotion Driver Service
"""
EmotionDriverService - Background service for emotion driving.

Manages EmotionDriver instances for all NPCs and runs
a background thread that ticks all active drivers.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import threading
import time
import logging

from .driver import EmotionDriver, get_driver, remove_driver, BehaviorTrigger

logger = logging.getLogger(__name__)


class EmotionDriverService:
    """
    Background service for emotion driving.
    
    Manages all EmotionDriver instances and runs a background
    thread that ticks them periodically.
    
    Features:
    - Background ticking of all active NPCs
    - Event-driven updates (pause decay on events, resume after)
    - Callback system for triggers and emotion changes
    - Start/stop control
    
    Example:
        >>> service = EmotionDriverService()
        >>> service.start()
        >>> 
        >>> # Register callback for triggers
        >>> def on_trigger(npc_id, trigger):
        ...     print(f"{npc_id}: {trigger.emotion} triggered at {trigger.threshold}")
        >>> service.register_trigger_callback(on_trigger)
        >>> 
        >>> # Process a game event
        >>> service.apply_event("tavern_keeper", {"anger": 0.3, "joy": 0.2})
        >>> 
        >>> # Get trajectory prediction
        >>> trajectory = service.get_trajectory("tavern_keeper", duration_seconds=60)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global service instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tick_interval = 1.0  # seconds between ticks
        
        # Driver instances: npc_id -> EmotionDriver
        self._drivers: Dict[str, EmotionDriver] = {}
        
        # Event callback registry
        self._emotion_change_callbacks: List[Callable] = []
        self._trigger_callbacks: List[Callable] = []
        self._relation_update_callbacks: List[Callable] = []
        
        # Active NPCs tracking
        self._active_npcs: set = set()
        self._last_activity: Dict[str, datetime] = {}
        
        # Lock for thread safety
        self._lock_obj = threading.RLock()
    
    def start(self, tick_interval: float = 1.0):
        """
        Start the background ticking service.
        
        Args:
            tick_interval: Seconds between ticks (default 1.0)
        """
        if self._running:
            logger.warning("EmotionDriverService already running")
            return
        
        self._tick_interval = tick_interval
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"EmotionDriverService started with {tick_interval}s tick interval")
    
    def stop(self):
        """Stop the background ticking service."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("EmotionDriverService stopped")
    
    def _run_loop(self):
        """Main loop running in background thread."""
        last_tick = time.time()
        
        while self._running:
            try:
                current_time = time.time()
                elapsed = current_time - last_tick
                last_tick = current_time
                
                self._tick_all(elapsed)
                
                # Sleep for remainder of tick interval
                sleep_time = max(0, self._tick_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Error in emotion driver loop: {e}")
                time.sleep(1.0)  # Brief pause on error
    
    def _tick_all(self, delta_seconds: float):
        """Tick all active drivers."""
        with self._lock_obj:
            npcs_to_tick = list(self._active_npcs)
        
        for npc_id in npcs_to_tick:
            try:
                self._tick_npc(npc_id, delta_seconds)
            except Exception as e:
                logger.error(f"Error ticking NPC {npc_id}: {e}")
    
    def _tick_npc(self, npc_id: str, delta_seconds: float):
        """Tick a single NPC's driver."""
        with self._lock_obj:
            if npc_id not in self._drivers:
                return
            driver = self._drivers[npc_id]
        
        # Get state before tick
        prev_state = driver.get_all_emotions()
        
        # Tick the driver
        triggers = driver.tick(delta_seconds)
        
        # Get state after tick
        current_state = driver.get_all_emotions()
        
        # Notify callbacks
        if self._emotion_change_callbacks:
            changes = self._detect_changes(prev_state, current_state)
            if changes:
                for callback in self._emotion_change_callbacks:
                    try:
                        callback(npc_id, changes, current_state)
                    except Exception as e:
                        logger.error(f"Error in emotion change callback: {e}")
        
        if triggers and self._trigger_callbacks:
            for trigger in triggers:
                for callback in self._trigger_callbacks:
                    try:
                        callback(npc_id, trigger)
                    except Exception as e:
                        logger.error(f"Error in trigger callback: {e}")
    
    def _detect_changes(
        self, 
        prev: Dict[str, float], 
        current: Dict[str, float]
    ) -> Dict[str, float]:
        """Detect which emotions changed significantly."""
        changes = {}
        threshold = 0.01  # Minimum change to report
        
        for emotion in set(prev.keys()) | set(current.keys()):
            prev_val = prev.get(emotion, 0.0)
            curr_val = current.get(emotion, 0.0)
            diff = curr_val - prev_val
            
            if abs(diff) >= threshold:
                changes[emotion] = diff
        
        return changes
    
    def register_npc(
        self,
        npc_id: str,
        personality_neuroticism: float = 0.5,
        initial_emotions: Optional[Dict[str, float]] = None,
    ) -> EmotionDriver:
        """
        Register an NPC with the service.
        
        Creates a new EmotionDriver if not exists.
        
        Args:
            npc_id: NPC identifier
            personality_neuroticism: OCEAN neuroticism (0-1)
            initial_emotions: Optional initial emotion state
            
        Returns:
            The EmotionDriver instance
        """
        with self._lock_obj:
            if npc_id not in self._drivers:
                self._drivers[npc_id] = EmotionDriver(
                    npc_id=npc_id,
                    personality_neuroticism=personality_neuroticism,
                    initial_emotions=initial_emotions,
                )
                logger.debug(f"Registered NPC {npc_id} with emotion driver")
            
            self._active_npcs.add(npc_id)
            self._last_activity[npc_id] = datetime.now()
            
            return self._drivers[npc_id]
    
    def unregister_npc(self, npc_id: str):
        """
        Unregister an NPC from the service.
        
        Removes from active list but keeps driver in memory.
        """
        with self._lock_obj:
            if npc_id in self._active_npcs:
                self._active_npcs.discard(npc_id)
                logger.debug(f"Unregistered NPC {npc_id} from active tracking")
    
    def remove_npc(self, npc_id: str):
        """
        Completely remove an NPC's driver.
        """
        with self._lock_obj:
            if npc_id in self._drivers:
                del self._drivers[npc_id]
            self._active_npcs.discard(npc_id)
            self._last_activity.pop(npc_id, None)
            logger.debug(f"Removed NPC {npc_id} from emotion driver service")
    
    def get_driver(self, npc_id: str) -> Optional[EmotionDriver]:
        """Get an NPC's driver."""
        with self._lock_obj:
            return self._drivers.get(npc_id)
    
    def apply_event(
        self,
        npc_id: str,
        emotion_deltas: Dict[str, float],
        pause_duration: float = 0.5,
    ):
        """
        Apply a game event to an NPC's emotions.
        
        Pauses decay briefly to allow the event effect to settle,
        then resumes decay.
        
        Args:
            npc_id: NPC identifier
            emotion_deltas: Dict of emotion -> delta to apply
            pause_duration: How long to pause decay (seconds)
        """
        with self._lock_obj:
            if npc_id not in self._drivers:
                # Auto-register if not exists
                self._drivers[npc_id] = EmotionDriver(npc_id=npc_id)
                self._active_npcs.add(npc_id)
            
            driver = self._drivers[npc_id]
        
        # Apply the event
        driver.apply_event_delta(emotion_deltas)
        driver.pause_decay(pause_duration)
        
        # Update activity
        with self._lock_obj:
            self._last_activity[npc_id] = datetime.now()
        
        # Notify emotion change callbacks
        if self._emotion_change_callbacks:
            current = driver.get_all_emotions()
            for callback in self._emotion_change_callbacks:
                try:
                    callback(npc_id, emotion_deltas, current)
                except Exception as e:
                    logger.error(f"Error in emotion change callback: {e}")
    
    def get_trajectory(
        self,
        npc_id: str,
        duration_seconds: float = 60.0,
        steps: int = 10,
    ) -> Optional[List[Dict]]:
        """
        Get predicted emotion trajectory for an NPC.
        
        Args:
            npc_id: NPC identifier
            duration_seconds: How far to predict
            steps: Number of trajectory points
            
        Returns:
            List of trajectory point dicts or None if NPC not found
        """
        with self._lock_obj:
            if npc_id not in self._drivers:
                return None
            driver = self._drivers[npc_id]
        
        trajectory = driver.get_emotion_trajectory(duration_seconds, steps)
        return [point.to_dict() for point in trajectory]
    
    def get_emotion_state(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Get current emotion state for an NPC."""
        with self._lock_obj:
            if npc_id not in self._drivers:
                return None
            return self._drivers[npc_id].get_emotion_state()
    
    def get_all_emotions(self, npc_id: str) -> Optional[Dict[str, float]]:
        """Get all emotion values for an NPC."""
        with self._lock_obj:
            if npc_id not in self._drivers:
                return None
            return self._drivers[npc_id].get_all_emotions()
    
    def get_active_triggers(self, npc_id: str, min_threshold: float = 0.5) -> List[Dict]:
        """Get active triggers for an NPC."""
        with self._lock_obj:
            if npc_id not in self._drivers:
                return []
            triggers = self._drivers[npc_id].get_active_triggers(min_threshold)
            return [t.to_dict() for t in triggers]
    
    def register_emotion_change_callback(self, callback: Callable):
        """Register a callback for emotion changes."""
        self._emotion_change_callbacks.append(callback)
    
    def register_trigger_callback(self, callback: Callable):
        """Register a callback for behavior triggers."""
        self._trigger_callbacks.append(callback)
    
    def register_relation_update_callback(self, callback: Callable):
        """Register a callback for relation updates."""
        self._relation_update_callbacks.append(callback)
    
    def get_active_npcs(self) -> List[str]:
        """Get list of active NPC IDs."""
        with self._lock_obj:
            return list(self._active_npcs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self._lock_obj:
            return {
                "running": self._running,
                "tick_interval": self._tick_interval,
                "total_drivers": len(self._drivers),
                "active_npcs": len(self._active_npcs),
                "registered_callbacks": {
                    "emotion_change": len(self._emotion_change_callbacks),
                    "trigger": len(self._trigger_callbacks),
                    "relation_update": len(self._relation_update_callbacks),
                },
            }


# Global service instance
_driver_service: Optional[EmotionDriverService] = None


def get_driver_service() -> EmotionDriverService:
    """Get the global EmotionDriverService instance."""
    global _driver_service
    if _driver_service is None:
        _driver_service = EmotionDriverService()
    return _driver_service


def start_driver_service(tick_interval: float = 1.0):
    """Start the global driver service."""
    service = get_driver_service()
    service.start(tick_interval)
    return service


def stop_driver_service():
    """Stop the global driver service."""
    global _driver_service
    if _driver_service:
        _driver_service.stop()
        _driver_service = None
