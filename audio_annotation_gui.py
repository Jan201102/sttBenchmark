import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pygame
import pandas as pd
import os
import threading
import time
from pathlib import Path

class AudioAnnotationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Annotation Tool")
        self.root.geometry("800x600")
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Paths
        self.wav_store_path = Path("wavStore")
        self.annotation_file = Path("annotation.csv")
        
        # Variables
        self.current_file_index = 0
        self.files_to_annotate = []
        self.is_playing = False
        self.current_sound = None
        
        # Load data
        self.load_files_to_annotate()
        
        # Create GUI
        self.create_widgets()
        
        # Load first file
        if self.files_to_annotate:
            self.load_current_file()
    
    def load_files_to_annotate(self):
        """Load WAV files that don't have annotations yet"""
        # Get all WAV files
        all_wav_files = set()
        if self.wav_store_path.exists():
            all_wav_files = {f.name for f in self.wav_store_path.glob("*.wav")}
        
        # Get annotated files
        annotated_files = set()
        if self.annotation_file.exists():
            try:
                df = pd.read_csv(self.annotation_file)
                if 'file_name' in df.columns:
                    annotated_files = set(df['file_name'].tolist())
            except Exception as e:
                print(f"Error reading annotation file: {e}")
        
        # Files that need annotation
        self.files_to_annotate = sorted(list(all_wav_files - annotated_files))
        
    def create_widgets(self):
        """Create the GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File info frame
        info_frame = ttk.LabelFrame(main_frame, text="File Information", padding="5")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # Current file label
        ttk.Label(info_frame, text="Current File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.current_file_label = ttk.Label(info_frame, text="No files to annotate")
        self.current_file_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Progress label
        ttk.Label(info_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.progress_label = ttk.Label(info_frame, text="0 / 0")
        self.progress_label.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Audio controls frame
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Controls", padding="5")
        audio_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio control buttons
        button_frame = ttk.Frame(audio_frame)
        button_frame.grid(row=0, column=0, pady=5)
        
        self.play_button = ttk.Button(button_frame, text="Play", command=self.play_audio)
        self.play_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_audio)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        # Volume control
        volume_frame = ttk.Frame(audio_frame)
        volume_frame.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(volume_frame, text="Volume:").grid(row=0, column=0, padx=(0, 5))
        self.volume_var = tk.DoubleVar(value=0.7)
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, variable=self.volume_var, 
                                command=self.update_volume, orient=tk.HORIZONTAL, length=200)
        volume_scale.grid(row=0, column=1)
        
        # Transcript frame
        transcript_frame = ttk.LabelFrame(main_frame, text="Transcript", padding="5")
        transcript_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        transcript_frame.columnconfigure(0, weight=1)
        transcript_frame.rowconfigure(0, weight=1)
        
        # Transcript text area
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, wrap=tk.WORD, 
                                                        height=10, width=70)
        self.transcript_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Navigation and action buttons
        nav_frame = ttk.Frame(action_frame)
        nav_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        self.prev_button = ttk.Button(nav_frame, text="← Previous", command=self.previous_file)
        self.prev_button.grid(row=0, column=0, padx=(0, 5))
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_file)
        self.next_button.grid(row=0, column=1, padx=(0, 5))
        
        self.skip_button = ttk.Button(nav_frame, text="Skip", command=self.skip_file)
        self.skip_button.grid(row=0, column=2)
        
        # Main action buttons
        self.save_button = ttk.Button(action_frame, text="Save Transcript", 
                                     command=self.save_transcript, style="Accent.TButton")
        self.save_button.grid(row=1, column=0, padx=(0, 10))
        
        self.delete_button = ttk.Button(action_frame, text="Delete File", 
                                       command=self.delete_file)
        self.delete_button.grid(row=1, column=1)
        
        # Configure grid weights for responsive layout
        main_frame.rowconfigure(2, weight=1)
        
        # Keyboard shortcuts
        self.root.bind('<Control-s>', lambda e: self.save_transcript())
        self.root.bind('<Control-d>', lambda e: self.delete_file())
        self.root.bind('<space>', lambda e: self.toggle_playback())
        self.root.bind('<Control-Right>', lambda e: self.next_file())
        self.root.bind('<Control-Left>', lambda e: self.previous_file())
        
        # Focus on transcript text area
        self.transcript_text.focus()
    
    def load_current_file(self):
        """Load the current file information"""
        if not self.files_to_annotate:
            self.current_file_label.config(text="No files to annotate")
            self.progress_label.config(text="0 / 0")
            self.disable_controls()
            return
        
        if 0 <= self.current_file_index < len(self.files_to_annotate):
            current_file = self.files_to_annotate[self.current_file_index]
            self.current_file_label.config(text=current_file)
            self.progress_label.config(text=f"{self.current_file_index + 1} / {len(self.files_to_annotate)}")
            self.transcript_text.delete(1.0, tk.END)
            self.enable_controls()
        else:
            self.current_file_label.config(text="All files completed!")
            self.progress_label.config(text=f"{len(self.files_to_annotate)} / {len(self.files_to_annotate)}")
            self.disable_controls()
    
    def enable_controls(self):
        """Enable all controls"""
        self.play_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.save_button.config(state="normal")
        self.delete_button.config(state="normal")
        self.transcript_text.config(state="normal")
        
        # Navigation buttons
        self.prev_button.config(state="normal" if self.current_file_index > 0 else "disabled")
        self.next_button.config(state="normal" if self.current_file_index < len(self.files_to_annotate) - 1 else "disabled")
        self.skip_button.config(state="normal")
    
    def disable_controls(self):
        """Disable all controls"""
        self.play_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.delete_button.config(state="disabled")
        self.prev_button.config(state="disabled")
        self.next_button.config(state="disabled")
        self.skip_button.config(state="disabled")
        self.transcript_text.config(state="disabled")
    
    def play_audio(self):
        """Play the current audio file"""
        if not self.files_to_annotate or self.current_file_index >= len(self.files_to_annotate):
            return
        
        current_file = self.files_to_annotate[self.current_file_index]
        file_path = self.wav_store_path / current_file
        
        if not file_path.exists():
            messagebox.showerror("Error", f"File not found: {current_file}")
            return
        
        try:
            self.stop_audio()  # Stop any currently playing audio
            self.current_sound = pygame.mixer.Sound(str(file_path))
            self.current_sound.set_volume(self.volume_var.get())
            self.current_sound.play()
            self.is_playing = True
            self.play_button.config(text="Playing...")
            
            # Start a thread to check when playback finishes
            threading.Thread(target=self.check_playback_status, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play audio: {str(e)}")
    
    def stop_audio(self):
        """Stop audio playback"""
        if self.current_sound:
            self.current_sound.stop()
        pygame.mixer.stop()
        self.is_playing = False
        self.play_button.config(text="Play")
    
    def toggle_playback(self):
        """Toggle between play and stop"""
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()
    
    def check_playback_status(self):
        """Check if audio is still playing (runs in separate thread)"""
        while self.is_playing and pygame.mixer.get_busy():
            time.sleep(0.1)
        
        if self.is_playing:  # If we exit the loop and is_playing is still True, playback finished naturally
            self.is_playing = False
            self.root.after(0, lambda: self.play_button.config(text="Play"))
    
    def update_volume(self, value):
        """Update volume"""
        if self.current_sound:
            self.current_sound.set_volume(float(value))
    
    def save_transcript(self):
        """Save the transcript to annotation.csv"""
        if not self.files_to_annotate or self.current_file_index >= len(self.files_to_annotate):
            return
        
        transcript = self.transcript_text.get(1.0, tk.END).strip()
        if not transcript:
            messagebox.showwarning("Warning", "Please enter a transcript before saving.")
            return
        
        current_file = self.files_to_annotate[self.current_file_index]
        
        try:
            # Load existing annotations or create new DataFrame
            if self.annotation_file.exists():
                df = pd.read_csv(self.annotation_file)
            else:
                df = pd.DataFrame(columns=['file_name', 'transcript'])
            
            # Add new annotation
            new_row = pd.DataFrame({'file_name': [current_file], 'transcript': [transcript]})
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to CSV
            df.to_csv(self.annotation_file, index=False)
            
            #messagebox.showinfo("Success", f"Transcript saved for {current_file}")
            
            # Remove from files to annotate and move to next
            self.files_to_annotate.pop(self.current_file_index)
            
            # Adjust current index if needed
            if self.current_file_index >= len(self.files_to_annotate):
                self.current_file_index = len(self.files_to_annotate) - 1
            
            self.stop_audio()
            self.load_current_file()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transcript: {str(e)}")
    
    def delete_file(self):
        """Delete the current WAV file"""
        if not self.files_to_annotate or self.current_file_index >= len(self.files_to_annotate):
            return
        
        current_file = self.files_to_annotate[self.current_file_index]
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion", 
                                  f"Are you sure you want to delete {current_file}?\n\nThis action cannot be undone."):
            return
        
        file_path = self.wav_store_path / current_file
        
        try:
            self.stop_audio()  # Stop playback before deleting
            
            if file_path.exists():
                file_path.unlink()  # Delete the file
                messagebox.showinfo("Success", f"File {current_file} deleted successfully.")
            else:
                messagebox.showwarning("Warning", f"File {current_file} not found.")
            
            # Remove from files to annotate and move to next
            self.files_to_annotate.pop(self.current_file_index)
            
            # Adjust current index if needed
            if self.current_file_index >= len(self.files_to_annotate):
                self.current_file_index = len(self.files_to_annotate) - 1
            
            self.load_current_file()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {str(e)}")
    
    def next_file(self):
        """Go to next file"""
        if self.current_file_index < len(self.files_to_annotate) - 1:
            self.current_file_index += 1
            self.stop_audio()
            self.load_current_file()
    
    def previous_file(self):
        """Go to previous file"""
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.stop_audio()
            self.load_current_file()
    
    def skip_file(self):
        """Skip current file without saving"""
        self.next_file()

def main():
    # Create and run the application
    root = tk.Tk()
    app = AudioAnnotationGUI(root)
    
    # Add help text
    help_text = """
Keyboard Shortcuts:
• Ctrl+S: Save transcript
• Ctrl+D: Delete file
• Space: Play/Stop audio
• Ctrl+→: Next file
• Ctrl+←: Previous file
"""
    
    def show_help():
        messagebox.showinfo("Help", help_text)
    
    # Add help menu
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Keyboard Shortcuts", command=show_help)
    
    root.mainloop()

if __name__ == "__main__":
    main()
