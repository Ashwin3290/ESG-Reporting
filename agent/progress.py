import streamlit as st
from typing import Optional, List, Dict
import time

class ProgressTracker:
    """Handle progress tracking and UI updates"""
    
    def __init__(self):
        self.status_placeholder: Optional[st.empty] = None
        self.progress_bar: Optional[st.progress] = None
        self.thought_placeholder: Optional[st.empty] = None
        
    def init_tracking(self):
        """Initialize tracking UI elements"""
        self.status_placeholder = st.empty()
        self.progress_bar = st.progress(0)
        self.thought_placeholder = st.empty()
        
    def update_status(self, stage: str, status: str, progress: float):
        """Update status display"""
        if self.status_placeholder:
            self.status_placeholder.info(f"{stage}: {status}")
        if self.progress_bar:
            self.progress_bar.progress(progress)
            
    def show_thought(self, thought: str):
        """Display current thought process"""
        if self.thought_placeholder:
            self.thought_placeholder.markdown(f"💭 {thought}")
            
    def clear(self):
        """Clear all progress elements"""
        if self.status_placeholder:
            self.status_placeholder.empty()
        if self.progress_bar:
            self.progress_bar.empty()
        if self.thought_placeholder:
            self.thought_placeholder.empty()

class AnalysisStage:
    """Track progress for a specific analysis stage"""
    
    def __init__(self, name: str, steps: List[str], tracker: ProgressTracker):
        self.name = name
        self.steps = steps
        self.tracker = tracker
        self.total_steps = len(steps)
        
    def execute(self, callback):
        """Execute stage with progress tracking"""
        for i, step in enumerate(self.steps):
            self.tracker.update_status(
                self.name,
                step,
                (i + 1) / self.total_steps
            )
            self.tracker.show_thought(f"Currently: {step}")
            result = callback(step)
            time.sleep(0.5)
            return result