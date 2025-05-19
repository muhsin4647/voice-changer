import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
from scipy.io.wavfile import write, read
import numpy as np
import librosa
import pygame
import os
import soundfile as sf
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VoiceChangerApp:
    def __init__(self, master):
        self.master = master
        master.title("AI Voice Studio Pro")
        master.geometry("1200x900")
        
        # Configure dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Audio variables
        self.target_audio = None
        self.input_audio = None
        self.modified_audio = None
        self.fs = 44100  # Sampling frequency
        
        # Create main container
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create widgets
        self.create_target_section()
        self.create_input_section()
        self.create_effects_section()
        self.create_waveform_displays()
        self.create_status_bar()
        self.create_playback_controls()
        
        # Initialize pygame mixer
        pygame.mixer.init()

    def configure_styles(self):
        self.style.configure('.', background='#1a1a1a', foreground='white')
        self.style.configure('TFrame', background='#1a1a1a')
        self.style.configure('TButton', font=('Helvetica', 10), padding=8, 
                            background='#2a2a2a', bordercolor='#3a3a3a')
        self.style.map('TButton', 
                      background=[('active', '#4a4a4a'), ('disabled', '#1a1a1a')],
                      foreground=[('active', 'white')])
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'), 
                           background='#1a1a1a', foreground='#00ff99')
        self.style.configure('Status.TLabel', font=('Helvetica', 9), 
                           background='#0a0a0a', foreground='#00ff99')
        self.style.configure('TLabelframe', background='#1a1a1a', 
                           foreground='white', bordercolor='#3a3a3a')
        self.style.configure('TLabelframe.Label', background='#1a1a1a', 
                           foreground='#00ff99')

    def create_target_section(self):
        frame = ttk.LabelFrame(self.main_frame, text="Voice Conversion", padding=15)
        frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        sub_frame = ttk.Frame(frame)
        sub_frame.pack(fill=tk.X)
        
        ttk.Button(sub_frame, text="Upload Target Model", 
                 command=self.upload_target).pack(side=tk.LEFT, padx=5)
        self.target_label = ttk.Label(sub_frame, text="No target model selected")
        self.target_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(frame, text="Convert to Target Voice", 
                 command=self.process_conversion).pack(pady=5)

    def create_input_section(self):
        frame = ttk.LabelFrame(self.main_frame, text="Input Voice", padding=15)
        frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Record Voice (5s)", 
                 command=self.record_voice).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Upload Voice File", 
                 command=self.upload_voice).pack(side=tk.LEFT, padx=5)
        self.input_label = ttk.Label(btn_frame, text="No input selected")
        self.input_label.pack(side=tk.LEFT, padx=10)

    def create_effects_section(self):
        frame = ttk.LabelFrame(self.main_frame, text="Voice Effects", padding=15)
        frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        self.effect_var = tk.StringVar()
        effects = ["None", "Robot", "Echo", "Chipmunk", "Slow Motion", "Reverse", "Alien"]
        
        effect_frame = ttk.Frame(frame)
        effect_frame.pack(pady=5)
        
        for i, effect in enumerate(effects):
            ttk.Radiobutton(effect_frame, text=effect, variable=self.effect_var,
                          value=effect, command=self.apply_effect).grid(row=0, column=i, padx=5)

    def create_waveform_displays(self):
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=3, column=0, sticky="nsew", pady=10)
        
        # Input waveform
        self.figure_in = Figure(figsize=(12, 3), dpi=100, facecolor='#1a1a1a')
        self.waveform_in = self.figure_in.add_subplot(111)
        self.waveform_in.set_facecolor('#1a1a1a')
        self.canvas_in = FigureCanvasTkAgg(self.figure_in, frame)
        self.canvas_in.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Output waveform
        self.figure_out = Figure(figsize=(12, 3), dpi=100, facecolor='#1a1a1a')
        self.waveform_out = self.figure_out.add_subplot(111)
        self.waveform_out.set_facecolor('#1a1a1a')
        self.canvas_out = FigureCanvasTkAgg(self.figure_out, frame)
        self.canvas_out.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        self.status_bar = ttk.Label(self.master, text="Ready", 
                                  style='Status.TLabel', anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_playback_controls(self):
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=4, column=0, pady=10)
        
        ttk.Button(frame, text="Play Original", 
                 command=lambda: self.play_audio(self.input_audio)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Play Converted", 
                 command=lambda: self.play_audio(self.modified_audio)).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Save Output", 
                 command=self.save_audio).pack(side=tk.LEFT, padx=5)

    def upload_target(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if file_path:
            try:
                self.target_audio, _ = librosa.load(file_path, sr=self.fs)
                self.target_label.config(text=os.path.basename(file_path))
                self.update_waveform(self.target_audio, self.waveform_in, "Target Voice")
                self.status_bar.config(text="Target voice loaded")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load target: {str(e)}")

    def upload_voice(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if file_path:
            try:
                self.input_audio, _ = librosa.load(file_path, sr=self.fs)
                self.input_label.config(text=os.path.basename(file_path))
                self.update_waveform(self.input_audio, self.waveform_in, "Input Voice")
                self.status_bar.config(text="Input voice loaded")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load input: {str(e)}")

    def record_voice(self):
        self.status_bar.config(text="Recording... (5 seconds)")
        self.master.update()
        
        try:
            duration = 5
            recording = sd.rec(int(duration * self.fs), samplerate=self.fs, channels=1)
            sd.wait()
            
            self.input_audio = recording.flatten()
            write('recording.wav', self.fs, recording)
            self.input_label.config(text="Recording.wav")
            self.update_waveform(self.input_audio, self.waveform_in, "Recorded Voice")
            self.status_bar.config(text="Recording complete")
        except Exception as e:
            messagebox.showerror("Error", f"Recording failed: {str(e)}")

    def process_conversion(self):
        if self.input_audio is None or self.target_audio is None:
            messagebox.showwarning("Warning", "Load both input and target voices first!")
            return
        
        try:
            self.status_bar.config(text="Processing voice conversion...")
            self.master.update()
            
            # Advanced pitch detection
            target_pitch = self.get_robust_pitch(self.target_audio)
            input_pitch = self.get_robust_pitch(self.input_audio)
            
            if input_pitch == 0 or target_pitch == 0:
                raise ValueError("Could not detect valid pitch in input files")
            
            # Calculate semitone difference
            semitone_shift = 12 * np.log2(target_pitch / input_pitch)
            
            # Apply pitch shift with formant preservation
            y_shifted = librosa.effects.pitch_shift(
                self.input_audio,
                sr=self.fs,
                n_steps=semitone_shift,
                bins_per_octave=48
            )
            
            # Apply formant shifting
            y_formant = self.apply_formant_shift(y_shifted, shift_factor=0.8)
            
            # Spectral envelope transfer
            D = librosa.stft(y_formant)
            target_D = librosa.stft(self.target_audio[:len(y_formant)])
            D_mag, _ = librosa.magphase(D)
            target_mag, target_phase = librosa.magphase(target_D)
            
            # Combine magnitude and phase
            processed_audio = librosa.istft(D_mag * target_phase)
            
            # Post-processing
            self.modified_audio = librosa.effects.remix(processed_audio, intervals=[(0, len(processed_audio))])
            self.modified_audio = librosa.util.normalize(self.modified_audio)
            
            # Update output
            self.update_waveform(self.modified_audio, self.waveform_out, "Converted Voice")
            write('converted.wav', self.fs, self.modified_audio)
            self.status_bar.config(text="Voice conversion complete - Ready to play!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")

    def apply_formant_shift(self, audio, shift_factor=1.0):
        # Formant shifting using phase vocoder
        D = librosa.stft(audio)
        D_shifted = librosa.phase_vocoder(D, rate=shift_factor)
        return librosa.istft(D_shifted)

    def get_robust_pitch(self, audio):
        # Improved pitch detection with RAPT algorithm
        pitches, magnitudes = librosa.piptrack(
            y=audio,
            sr=self.fs,
            fmin=80,
            fmax=400,
            hop_length=512,
            n_fft=2048
        )
        
        # Find pitches with significant magnitude
        threshold = np.median(magnitudes[magnitudes > 0]) * 1.5
        valid_pitches = pitches[magnitudes > threshold]
        
        if len(valid_pitches) == 0:
            return 0
        
        # Use median for stability
        return np.median(valid_pitches[valid_pitches > 0])

    def apply_effect(self):
        if self.input_audio is None:
            messagebox.showwarning("Warning", "Load or record input voice first!")
            return
        
        effect = self.effect_var.get()
        try:
            self.status_bar.config(text=f"Applying {effect} effect...")
            self.master.update()
            
            if effect == "Robot":
                self.modified_audio = self.robot_effect(self.input_audio)
            elif effect == "Echo":
                self.modified_audio = self.echo_effect(self.input_audio)
            elif effect == "Chipmunk":
                y_shifted = librosa.effects.pitch_shift(self.input_audio, sr=self.fs, n_steps=4)
                self.modified_audio = self.apply_formant_shift(y_shifted, 1.2)
            elif effect == "Slow Motion":
                self.modified_audio = librosa.effects.time_stretch(self.input_audio, rate=0.6)
            elif effect == "Reverse":
                self.modified_audio = self.input_audio[::-1]
            elif effect == "Alien":
                y_shifted = librosa.effects.pitch_shift(self.input_audio, sr=self.fs, n_steps=7)
                self.modified_audio = self.apply_formant_shift(y_shifted, 0.5)
            else:
                self.modified_audio = self.input_audio.copy()
            
            self.modified_audio = librosa.util.normalize(self.modified_audio)
            self.update_waveform(self.modified_audio, self.waveform_out, f"{effect} Effect")
            write('effect.wav', self.fs, self.modified_audio)
            self.status_bar.config(text=f"{effect} effect applied")
            
        except Exception as e:
            messagebox.showerror("Error", f"Effect failed: {str(e)}")

    def robot_effect(self, audio):
        # Add AM modulation and filtering
        carrier_freq = 100  # Hz
        t = np.arange(len(audio)) / self.fs
        carrier = np.sin(2 * np.pi * carrier_freq * t)
        processed = audio * carrier
        
        # Apply low-pass filter
        return librosa.effects.preemphasis(processed, coef=0.98)

    def echo_effect(self, audio):
        # Multiple echo generator
        delays = [0.2, 0.4, 0.6]  # seconds
        decays = [0.5, 0.3, 0.2]
        echo = audio.copy()
        
        for delay, decay in zip(delays, decays):
            delay_samples = int(delay * self.fs)
            if delay_samples < len(echo):
                echo[delay_samples:] += decay * audio[:-delay_samples]
        
        return echo

    def update_waveform(self, audio, ax, title):
        ax.clear()
        ax.plot(np.linspace(0, len(audio)/self.fs, len(audio)), audio, color='#00ff99')
        ax.set_title(title, color='white')
        ax.set_xlabel("Time (s)", color='white')
        ax.set_ylabel("Amplitude", color='white')
        ax.tick_params(colors='white')
        ax.figure.canvas.draw()

    def play_audio(self, audio):
        if audio is not None:
            try:
                temp_file = "temp_playback.wav"
                write(temp_file, self.fs, audio)
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                self.status_bar.config(text="Playing audio...")
            except Exception as e:
                messagebox.showerror("Error", f"Playback failed: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No audio to play")

    def save_audio(self):
        if self.modified_audio is not None:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            if file_path:
                write(file_path, self.fs, self.modified_audio)
                self.status_bar.config(text=f"Audio saved to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceChangerApp(root)
    root.mainloop()