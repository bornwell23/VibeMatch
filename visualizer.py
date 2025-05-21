"""
Real-time audio visualizer that displays dynamic visualizations synchronized with audio playback.
Supports multiple visualization styles that respond to audio features like tempo, energy, and frequency content.
"""

import pygame
import numpy as np
import threading
import queue
import time
from pathlib import Path
from typing import Tuple, List, Optional
import pygame.gfxdraw
import colorsys
import random
from dataclasses import dataclass
try:
    from analyze import load_analysis, get_tempo_and_beat_indices
    from utilities import Logger, FileFormats
except ImportError:
    from VibeMatch.analyze import load_analysis, get_tempo_and_beat_indices
    from VibeMatch.utilities import Logger, FileFormats

# import librosa
import sounddevice as sd
from pydub import AudioSegment

@dataclass
class AudioData:
    """Container for audio analysis data used by visualizations"""
    raw_audio: np.ndarray
    sample_rate: int
    tempo: float
    beat_frames: np.ndarray
    current_frame: int = 0
    
class AudioVisualizer:
    def __init__(self, width: int = 1280, height: int = 720):
        """Initialize the visualizer with given dimensions"""
        pygame.init()
        self.width = width
        self.height = height
        self.fullscreen = True  # Start in fullscreen by default
        
        # Make window resizable
        self._setup_display()
        
        # Initialize fonts
        pygame.font.init()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Visualization parameters
        # FFT parameters
        self.fft_window_size = 2048
        self.fft_output_size = 1024
        
        self.log_scale_factor = 1.5  # Controls the logarithmic curve steepness

        # Circular wave parameters
        self.wave_num_points = 180
        self.wave_base_radius = 150
        self.wave_frequency_impact = 100
        self.wave_layers = 4  # Number of concentric wave layers
        self.wave_layer_spacing = 40  # Spacing between layers
        self.wave_base_speed = 0.3  # Base rotation speed
        self.wave_speed_increment = 0.2  # Speed increase per layer
        self.wave_movement_speed = 2.0  # Base wave movement speed
        self.wave_movement_increment = 0.5  # Movement speed increase per layer
        self.wave_thickness = 3  # Base thickness of wave lines
        
        # Wave border parameters
        self.wave_border_distance = 20  # Distance from window edge
        self.wave_border_segments = 100  # Number of border segments
        self.wave_border_height = 30  # Maximum height of border bars
        self.wave_border_spacing = 2  # Spacing between border bars
        self.wave_border_speed = 1.5  # Speed of border movement
        
        # Frequency bars parameters
        self.bars_count = 64
        self.bars_spacing = 2
        self.bars_frequency_impact = 100  # Divisor for frequency's effect on height
        self.bars_max_height_ratio = 1.0  # Maximum height as ratio of screen height
        self.bars_min_height_ratio = 0.05  # Minimum height ratio
        self.bars_base_movement_speed = 2  # Speed of the base movement
        
        # Particle system parameters
        self.particle_count = 50
        self.particle_min_size = 2
        self.particle_size_impact = 1
        self.particle_base_distance = 150
        self.particle_frequency_impact = 200
        self.particle_base_speed = 0.3  # Base rotation speed
        self.particle_speed_increment = 0.2  # Speed increase per layer
        self.particle_wave_speed = 2.0  # Speed of wave motion
        self.particle_wave_amplitude = 30  # Amplitude of wave motion
        self.particle_spiral_speed = 1.0  # Speed of spiral motion
        self.particle_spiral_amplitude = 20  # Amplitude of spiral effect
        self.particle_border_distance = 30  # Distance from window border
        self.particle_border_count = 120  # Number of particles in border
        self.particle_border_wave_speed = 3.0  # Speed of border wave motion
        self.particle_border_wave_count = 3  # Number of waves along border
        self.particle_border_pulse_speed = 2.0  # Speed of pulsing motion
        self.particle_border_movement = 25  # Amplitude of border movement
        self.particle_layers = 3  # Number of particle layers
        self.particle_layer_spacing = 80  # Distance between layers
        
        # Waveform tunnel parameters
        self.tunnel_num_rings = 25  # More rings
        self.tunnel_points_per_ring = 180
        self.tunnel_ring_spacing = 25  # Increased spacing
        self.tunnel_frequency_impact = 40  # Increased distortion
        self.tunnel_line_thickness = 2
        self.tunnel_rotation_speed = 0.5  # Added: Rotation speed
        
        # Color parameters
        self.color_saturation = 0.8
        self.color_value = 0.9
        self.color_time_speed = 5  # Seconds for full color cycle
        
        self.clock = pygame.time.Clock()
        self.running = False
        self.current_vis_idx = 0
        self.current_vis = self._circular_wave
        self.audio_data: Optional[AudioData] = None
        self.audio_queue = queue.Queue()
        self.paused = False
        
        # Loading screen properties
        self.loading_progress = 0
        self.loading_text = ""
        self.file_info = {}
        
        # Visualization options
        self.visualizations = [
            self._circular_wave,
            self._frequency_bars,
            self._particle_system,
            self._waveform_tunnel
        ]

        self.update_visualization()

    def _setup_display(self):
        """Set up the display based on fullscreen setting."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            # Use 80% of screen size for windowed mode
            windowed_width = int(self.width * 0.8)
            windowed_height = int(self.height * 0.8)
            self.screen = pygame.display.set_mode((windowed_width, windowed_height))
            
        pygame.display.set_caption("Music Visualizer")

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        self._setup_display()

    def update_visualization(self, left=False):
        """Switch to the next visualization"""
        self.current_vis_idx = ((self.current_vis_idx + 1) if not left else (self.current_vis_idx - 1)) % len(self.visualizations)
        self.current_vis = self.visualizations[self.current_vis_idx]
        return self.current_vis 

    def get_visualization_name(self, visualization=None):
        """Get the name of the current visualization"""
        return (visualization or self.visualizations[self.current_vis_idx]).__name__.replace("_", " ").strip().capitalize()

    def _draw_loading_screen(self):
        """Draw the loading screen with progress and file information"""
        self.screen.fill((0, 0, 0))
        
        # Calculate center positions
        center_x = self.width // 2
        start_y = self.height // 3
        
        # Draw file name
        if 'file_name' in self.file_info:
            text = self.font_large.render(Path(self.file_info['file_name']).name, True, (255, 255, 255))
            rect = text.get_rect(center=(center_x, start_y))
            self.screen.blit(text, rect)
        
        # Draw loading progress bar
        bar_width = 400
        bar_height = 20
        border = 2
        progress_rect = pygame.Rect(center_x - bar_width//2, start_y + 80, bar_width, bar_height)
        pygame.draw.rect(self.screen, (100, 100, 100), progress_rect)
        inner_rect = pygame.Rect(
            progress_rect.left + border,
            progress_rect.top + border,
            int((progress_rect.width - 2*border) * self.loading_progress),
            bar_height - 2*border
        )
        pygame.draw.rect(self.screen, (0, 255, 100), inner_rect)
        
        # Draw loading text
        text = self.font_medium.render(self.loading_text, True, (200, 200, 200))
        rect = text.get_rect(center=(center_x, start_y + 120))
        self.screen.blit(text, rect)
        
        # Draw file information
        y_offset = start_y + 180
        for key, value in self.file_info.items():
            if key != 'file_name':  # Already showed filename at top
                info_text = f"{key}: {value}"
                text = self.font_small.render(info_text, True, (180, 180, 180))
                rect = text.get_rect(center=(center_x, y_offset))
                self.screen.blit(text, rect)
                y_offset += 30
        
        pygame.display.flip()
        self.clock.tick(60)

    def load_audio(self, file_path: str) -> None:
        """Load and analyze audio file"""
        file_name = Path(file_path).stem
        if ' - ' in file_name:
            file_name = ' by '.join(file_name.split(' - ', maxsplit=1)[::-1])
        self.file_info = {'file_name': file_name}
        self.loading_progress = 0
        self.loading_text = "Loading audio file..."
        self._draw_loading_screen()
        
        # Load basic file info
        audio_segment = AudioSegment.from_file(file_path)
        self.file_info.update({
            'Duration': f"{audio_segment.duration_seconds:.1f} seconds",
            'Channels': audio_segment.channels,
            'Sample Rate': f"{audio_segment.frame_rate} Hz",
            'Format': Path(file_path).suffix[1:].upper()
        })
        self.loading_progress = 0.2
        self._draw_loading_screen()
        
        # Load and analyze audio
        self.loading_text = "Analyzing audio data..."
        audio_data = load_analysis(file_path, audio_segment)
        self.loading_progress = 0.5
        self._draw_loading_screen()
        
        # Get tempo and beat information
        self.loading_text = "Detecting tempo and beats..."
        tempo, beat_frames = get_tempo_and_beat_indices(audio_data)
        self.loading_progress = 0.8
        self._draw_loading_screen()
        
        # Store audio data
        self.audio_data = AudioData(
            raw_audio=audio_data[0],
            sample_rate=audio_data[1],
            tempo=tempo,
            beat_frames=beat_frames
        )
        
        # Update file info with analysis results
        self.file_info['Tempo'] = f"{round(tempo, 2)} BPM"
        self.file_info['Detected Beats'] = f"{len(beat_frames)} beats"
        
        self.loading_progress = 1.0
        self.loading_text = "Ready to play!"
        self._draw_loading_screen()
        
        # Small delay to show completion
        time.sleep(0.5)
        
        Logger.write(f"Audio loaded - Tempo: {round(tempo, 2)} BPM")

    def _audio_playback(self):
        """Handle audio playback in a separate thread"""
        if self.audio_data:
            sd.play(self.audio_data.raw_audio, self.audio_data.sample_rate)
            while sd.get_stream().active and self.running:
                if self.paused:
                    sd.stop()
                    while self.paused and self.running:
                        time.sleep(0.1)
                    if self.running:
                        # Resume from where we left off
                        current_sample = int(self.audio_data.current_frame * 
                                          self.audio_data.sample_rate / 60)
                        remaining_audio = self.audio_data.raw_audio[current_sample:]
                        sd.play(remaining_audio, self.audio_data.sample_rate)
                time.sleep(0.1)
            
    def _get_current_spectrum(self) -> np.ndarray:
        """Get the current frequency spectrum of the audio being played."""
        if not self.audio_data:
            return np.zeros(self.fft_output_size)
            
        current_sample = int(self.audio_data.current_frame * 
                           self.audio_data.sample_rate / 60)
        
        if current_sample + self.fft_window_size >= len(self.audio_data.raw_audio):
            return np.zeros(self.fft_output_size)
            
        # Get raw spectrum
        spectrum = np.abs(np.fft.fft(
            self.audio_data.raw_audio[current_sample:current_sample + self.fft_window_size]
        ))[:self.fft_output_size]
        
        # Simple normalization
        spectrum = spectrum / np.max(spectrum) if np.max(spectrum) > 0 else spectrum
        
        return spectrum

    def _circular_wave(self, surface: pygame.Surface):
        """Circular waveform visualization that responds to beat and frequency content."""
        spectrum = self._get_current_spectrum()
        center = (self.width // 2, self.height // 2)
        time_offset = time.time()
        
        # Draw multiple wave layers
        for layer in range(self.wave_layers):
            layer_ratio = layer / (self.wave_layers - 1)  # 0 to 1
            base_radius = self.wave_base_radius + layer * self.wave_layer_spacing
            
            # Calculate layer-specific speeds
            direction = 1 if layer % 2 == 0 else -1  # Alternate direction
            rotation_speed = self.wave_base_speed + layer * self.wave_speed_increment
            movement_speed = self.wave_movement_speed + layer * self.wave_movement_increment
            
            # Layer-specific time offsets
            rotation = time_offset * rotation_speed * direction
            movement_offset = time_offset * movement_speed * direction
            
            # Pre-calculate all points for this layer
            main_points = []
            for i in range(self.wave_num_points):
                angle = 2 * np.pi * i / self.wave_num_points + rotation
                
                # Get frequency data
                freq_idx = int((i / self.wave_num_points) * len(spectrum))
                intensity = spectrum[freq_idx]
                
                # Add multiple wave effects with layer-specific speeds
                wave1 = np.sin(angle * 3 + movement_offset) * (20 + layer * 5) * intensity
                wave2 = np.cos(angle * 5 - movement_offset * 0.7) * (15 + layer * 3) * intensity
                wave3 = np.sin(angle * 7 + movement_offset * 1.3) * (10 + layer * 2) * intensity
                
                # Combine waves and add frequency impact
                radius = (base_radius + 
                         (wave1 + wave2 + wave3) + 
                         intensity * self.wave_frequency_impact * (1 + layer_ratio * 0.5))
                
                x = center[0] + np.cos(angle) * radius
                y = center[1] + np.sin(angle) * radius
                main_points.append((x, y, intensity))
            
            # Close the loop
            main_points.append(main_points[0])
            
            # Calculate the thickness for this layer
            thickness = int(self.wave_thickness * (1 + layer_ratio))
            
            # Draw the wave with thickness
            for t in range(thickness):
                t_ratio = t / thickness
                alpha = int(255 * (1 - t_ratio * 0.7))  # Fade out towards edges
                
                # Calculate normal vectors for each segment
                for i in range(len(main_points) - 1):
                    p1 = main_points[i]
                    p2 = main_points[i + 1]
                    
                    # Calculate normal vector
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    length = np.sqrt(dx * dx + dy * dy)
                    if length > 0:
                        normal_x = -dy / length
                        normal_y = dx / length
                    else:
                        continue
                    
                    # Calculate offset points
                    offset = (t - thickness/2) * 0.5
                    points = [
                        (p1[0] + normal_x * offset, p1[1] + normal_y * offset),
                        (p2[0] + normal_x * offset, p2[1] + normal_y * offset)
                    ]
                    
                    # Color with layer-specific hue and timing
                    intensity = (p1[2] + p2[2]) / 2  # Average intensity of segment
                    hsv = ((layer_ratio + time_offset / (5 + layer * 2)) % 1.0,
                          self.color_saturation,
                          max(0.4, min(0.9, 0.6 + intensity * 0.3)))
                    rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
                    color = (rgb[0], rgb[1], rgb[2], alpha)
                    
                    # Draw the line segment
                    pygame.draw.line(surface, color, points[0], points[1], 1)
        
        # Draw frequency border
        border_width = (self.width - 2 * self.wave_border_distance) // self.wave_border_segments
        border_offset = time_offset * self.wave_border_speed
        
        for i in range(self.wave_border_segments):
            # Get frequency data with smooth interpolation
            t = i / self.wave_border_segments
            freq_idx = int(t * len(spectrum))
            next_freq_idx = min(freq_idx + 1, len(spectrum) - 1)
            blend = (t * len(spectrum)) % 1
            intensity = spectrum[freq_idx] * (1 - blend) + spectrum[next_freq_idx] * blend
            
            # Calculate bar height with wave effect
            wave = np.sin(t * np.pi * 8 + border_offset) * 0.3 + 0.7
            height = int(self.wave_border_height * intensity * wave)
            
            # Calculate bar position
            x = self.wave_border_distance + i * (border_width + self.wave_border_spacing)
            
            # Draw top and bottom bars
            for edge in [(0, -1), (self.height, 1)]:  # (y_pos, direction)
                y = edge[0] + edge[1] * height
                rect = pygame.Rect(x, min(y, edge[0]), 
                                 border_width, abs(height))
                
                # Color based on position and intensity
                hsv = ((t + border_offset / 10) % 1.0,
                      self.color_saturation,
                      max(0.4, min(0.9, 0.5 + intensity * 0.4)))
                rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
                
                pygame.draw.rect(surface, rgb, rect)

    def _frequency_bars(self, surface: pygame.Surface):
        """Vertical frequency bars visualization that shows audio spectrum in real-time."""
        spectrum = self._get_current_spectrum()
        bar_width = self.width // self.bars_count
        
        # Create logarithmically spaced frequency bands
        freq_indices = np.logspace(0, np.log10(len(spectrum)), self.bars_count, dtype=int)
        freq_indices = np.clip(freq_indices, 0, len(spectrum) - 1)
        
        # Add time-based movement
        time_offset = time.time() * self.bars_base_movement_speed
        
        for i in range(self.bars_count):
            # Get frequency data with logarithmic spacing
            freq_idx = freq_indices[i]
            intensity = spectrum[freq_idx]
            
            # Apply logarithmic scaling to intensity
            intensity = np.log10(intensity * 9 + 1) * self.log_scale_factor
            
            # Add subtle base movement
            base_movement = (np.sin(time_offset + i * 0.2) * 0.1 + 1) * self.bars_min_height_ratio
            
            # Calculate final height with minimum value
            height = int(
                max(
                    self.height * self.bars_min_height_ratio,
                    min(
                        (intensity + base_movement) * self.height * self.bars_max_height_ratio,
                        self.height * self.bars_max_height_ratio
                    )
                )
            )
            
            # Color with minimum brightness
            color = pygame.Color(0)
            hsv = ((i / self.bars_count + time.time() / self.color_time_speed) % 1.0, 
                  self.color_saturation, 
                  max(0.4, min(0.9, 0.5 + intensity * 0.4)))  # Ensure good visibility
            rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
            
            # Draw bar with rounded corners
            rect = pygame.Rect(
                i * bar_width, 
                self.height - height, 
                bar_width - self.bars_spacing, 
                height
            )
            pygame.draw.rect(surface, rgb, rect, border_radius=2)

    def _get_border_position(self, t: float, width: int, height: int, border_distance: int) -> tuple[float, float]:
        """Calculate position along window border for given parameter t (0 to 1)"""
        # Adjusted dimensions for border path
        w = width - 2 * border_distance
        h = height - 2 * border_distance
        
        # Corner radius
        r = min(w, h) * 0.1
        
        # Adjusted dimensions accounting for corner radius
        wa = w - 2 * r
        ha = h - 2 * r
        
        # Total perimeter length
        perimeter = 2 * (wa + ha) + 2 * np.pi * r
        
        # Convert t to distance along perimeter
        d = t * perimeter
        
        # Calculate position based on distance along perimeter
        if d < wa:  # Top edge
            return border_distance + r + d, border_distance
        d -= wa
        
        if d < ha:  # Right edge
            return width - border_distance, border_distance + r + d
        d -= ha
        
        if d < wa:  # Bottom edge
            return width - border_distance - r - d, height - border_distance
        d -= wa
        
        if d < ha:  # Left edge
            return border_distance, height - border_distance - r - d
        d -= ha
        
        # Handle corners with circular arcs
        if d < r * np.pi / 2:  # Top-right corner
            angle = d / r
            return (width - border_distance - r + r * np.cos(angle),
                   border_distance + r - r * np.sin(angle))
        d -= r * np.pi / 2
        
        if d < r * np.pi / 2:  # Bottom-right corner
            angle = d / r
            return (width - border_distance - r + r * np.sin(angle),
                   height - border_distance - r + r * np.cos(angle))
        d -= r * np.pi / 2
        
        if d < r * np.pi / 2:  # Bottom-left corner
            angle = d / r
            return (border_distance + r - r * np.cos(angle),
                   height - border_distance - r + r * np.sin(angle))
        d -= r * np.pi / 2
        
        # Top-left corner
        angle = d / r
        return (border_distance + r - r * np.sin(angle),
                border_distance + r - r * np.cos(angle))

    def _particle_system(self, surface: pygame.Surface):
        """Particle system visualization that creates dynamic, music-reactive particles."""
        spectrum = self._get_current_spectrum()
        center = (self.width // 2, self.height // 2)
        
        # Add time-based movement
        time_offset = time.time()
        wave_offset = time_offset * self.particle_wave_speed
        spiral_offset = time_offset * self.particle_spiral_speed
        
        # Draw multiple layers of particles
        for layer in range(self.particle_layers):
            layer_ratio = layer / (self.particle_layers - 1)  # 0 to 1
            layer_distance = self.particle_base_distance + layer * self.particle_layer_spacing
            
            # Alternate direction and increase speed with each layer
            direction = 1 if layer % 2 == 0 else -1
            speed_factor = self.particle_base_speed + layer * self.particle_speed_increment
            layer_rotation = time_offset * speed_factor * direction
            
            for i in range(self.particle_count):
                # Get frequency data with logarithmic spacing
                freq_idx = i * len(spectrum) // self.particle_count
                intensity = spectrum[freq_idx]
                
                # Base angle with layer-specific rotation
                angle = 2 * np.pi * i / self.particle_count + layer_rotation
                
                # Add wave motion that follows rotation direction
                wave = np.sin(angle * 3 * direction + wave_offset) * self.particle_wave_amplitude * intensity
                
                # Add spiral effect that follows rotation direction
                spiral = np.sin(spiral_offset * direction + i * 0.1) * self.particle_spiral_amplitude * intensity
                
                # Calculate distance with all effects
                distance = (layer_distance + 
                          wave +
                          spiral +
                          intensity * self.particle_frequency_impact)
                
                # Add some wobble that follows rotation direction
                wobble_x = np.sin(time_offset * 2 * direction + i + layer) * 10 * intensity
                wobble_y = np.cos(time_offset * 2 * direction + i + layer) * 10 * intensity
                
                # Calculate position
                x = center[0] + np.cos(angle) * distance + wobble_x
                y = center[1] + np.sin(angle) * distance + wobble_y
                
                # Size varies with layer and intensity
                size = int(self.particle_min_size + intensity * 20 * (1 + layer_ratio * 0.5))
                
                # Color with layer-specific hue offset and rotation direction influence
                hue_offset = layer_ratio * 0.3 * direction
                hsv = (((i / self.particle_count + hue_offset + time_offset / (5 + layer)) % 1.0), 
                      self.color_saturation, 
                      max(0.4, min(0.9, 0.6 + intensity * 0.3)))
                rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
                
                pygame.gfxdraw.filled_circle(surface, int(x), int(y), size, rgb)
        
        # Draw border particles
        border_offset = time_offset * 0.3  # Slower movement for border
        
        for i in range(self.particle_border_count):
            # Get frequency data
            freq_idx = i * len(spectrum) // self.particle_border_count
            intensity = spectrum[freq_idx]
            
            # Calculate position along border with offset
            t = ((i / self.particle_border_count + border_offset) % 1.0)
            base_x, base_y = self._get_border_position(t, self.width, self.height, 
                                                     self.particle_border_distance)
            
            # Multiple wave effects
            wave1 = np.sin(t * np.pi * self.particle_border_wave_count * 2 + wave_offset * self.particle_border_wave_speed)
            wave2 = np.cos((t + 0.25) * np.pi * self.particle_border_wave_count + wave_offset * self.particle_border_wave_speed * 0.7)
            wave3 = np.sin(t * np.pi * 4 - wave_offset * self.particle_border_wave_speed * 1.3)
            
            combined_wave = (wave1 + wave2 + wave3) / 3 * self.particle_border_movement * (0.5 + intensity * 0.5)
            
            # Add pulsing effect
            pulse = np.sin(time_offset * self.particle_border_pulse_speed + t * np.pi * 2) * 10 * intensity
            
            # Determine direction of movement based on position
            if t < 0.25:  # Top edge
                x = base_x + wave2 * intensity * 10
                y = base_y + combined_wave + pulse
            elif t < 0.5:  # Right edge
                x = base_x - combined_wave - pulse
                y = base_y + wave2 * intensity * 10
            elif t < 0.75:  # Bottom edge
                x = base_x - wave2 * intensity * 10
                y = base_y - combined_wave - pulse
            else:  # Left edge
                x = base_x + combined_wave + pulse
                y = base_y - wave2 * intensity * 10
            
            # Add some chaotic motion
            chaos_x = np.sin(time_offset * 3 + t * 7) * intensity * 5
            chaos_y = np.cos(time_offset * 3 + t * 7) * intensity * 5
            x += chaos_x
            y += chaos_y
            
            # Size varies with wave intensity
            size = int(self.particle_min_size * 1.5 + 
                      intensity * 15 + 
                      abs(combined_wave) * 0.2)
            
            # Color scheme for border particles with wave-based variation
            wave_color = (abs(combined_wave) / (self.particle_border_movement * 1.5)) * 0.2
            hsv = ((1 - t + time_offset / 7 + wave_color) % 1.0,
                  self.color_saturation,
                  max(0.4, min(0.9, 0.5 + intensity * 0.4 + wave_color)))
            rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
            
            pygame.gfxdraw.filled_circle(surface, int(x), int(y), size, rgb)

    def _waveform_tunnel(self, surface: pygame.Surface):
        """3D tunnel effect using concentric rings that react to the audio."""
        spectrum = self._get_current_spectrum()
        center = (self.width // 2, self.height // 2)
        
        # Add rotation effect
        time_offset = time.time() * self.tunnel_rotation_speed
        
        for ring in range(self.tunnel_num_rings):
            points = []
            ring_radius = (self.tunnel_num_rings - ring) * self.tunnel_ring_spacing
            
            # Get frequency data with logarithmic spacing
            freq_idx = ring * len(spectrum) // self.tunnel_num_rings
            intensity = spectrum[freq_idx]
            
            for i in range(self.tunnel_points_per_ring):
                angle = 2 * np.pi * i / self.tunnel_points_per_ring + time_offset
                
                # Add wave motion
                wave = np.sin(angle * 3 + time_offset * 2) * 20 * intensity
                
                # Calculate distance with wave effect
                distance = ring_radius + intensity * self.tunnel_frequency_impact * 100 + wave
                
                x = center[0] + np.cos(angle) * distance
                y = center[1] + np.sin(angle) * distance
                points.append((x, y))
                
            hsv = ((ring / self.tunnel_num_rings + time_offset / self.color_time_speed) % 1.0, 
                  self.color_saturation, 
                  max(0.3, min(0.8, 0.5 + intensity * 0.3)))  # Controlled brightness
            rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(*hsv))
            
            if len(points) > 2:
                pygame.draw.lines(surface, rgb, True, points, self.tunnel_line_thickness)
                
    def _handle_resize(self, event):
        """Handle window resize event"""
        self.width = event.w
        self.height = event.h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
    def run(self, file_path: str):
        """Run the visualizer with the specified audio file"""
        supported_formats = ['.wav', '.mp3', '.m4a']
        file_path = Path(file_path)
        
        if not file_path.exists():
            Logger.write(f"Error: File {file_path} does not exist", level="ERROR")
            return
            
        if file_path.suffix.lower() not in supported_formats:
            Logger.write(f"Error: Unsupported file format. Supported formats: {supported_formats}", 
                        level="ERROR")
            return
            
        self.load_audio(str(file_path))
        
        # Start audio playback in a separate thread
        audio_thread = threading.Thread(target=self._audio_playback)
        audio_thread.start()
        
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Toggle pause state
                        self.paused = not self.paused
                        Logger.write("Playback " + ("paused" if self.paused else "resumed"))
                    elif event.key == pygame.K_ESCAPE:
                        if self.fullscreen:
                            self.toggle_fullscreen()
                        else:
                            self.running = False
                    elif event.key == pygame.K_LEFT:
                        # Previous visualization
                        self.update_visualization(left=True)
                        Logger.write(f"Switched to visualization {self.get_visualization_name()}")
                    elif event.key == pygame.K_RIGHT:
                        # Next visualization
                        self.update_visualization(left=False)
                        Logger.write(f"Switched to visualization {self.get_visualization_name()}")
                    elif event.key == pygame.K_f:
                        self.toggle_fullscreen()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event)
                        
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Update current frame counter only if not paused
            if self.audio_data and not self.paused:
                self.audio_data.current_frame += 1
                
            # Draw current visualization
            self.visualizations[self.current_vis_idx](self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)  # Maintain 60fps
            
        pygame.quit()
        sd.stop()
        
class SongSelector:
    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height
        self.fullscreen = True  # Start in fullscreen by default
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # UI parameters
        self.padding = 20
        self.item_height = 40
        self.search_height = 50
        self.visible_items = 15
        self.scroll_position = 0
        self.selected_index = 0
        
        # Search parameters
        self.search_text = ""
        self.search_active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Colors
        self.text_color = (200, 200, 200)
        self.selected_color = (100, 100, 255)
        self.search_color = (150, 150, 150)
        self.background_color = (30, 30, 30)
        
        # Load songs and folders
        self.base_path = Path("songs")
        self.items = self._scan_directory(self.base_path)
        self.filtered_items = self.items.copy()
    
    def _scan_directory(self, path: Path) -> List[Tuple[Path, bool]]:
        """Scan directory for music files and subdirectories."""
        items = []
        if not path.exists():
            path.mkdir(parents=True)
            return items
        
        for item in path.iterdir():
            if item.is_dir():
                items.append((item, True))  # True indicates it's a directory
            elif item.suffix.lower() in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
                items.append((item, False))  # False indicates it's a file
        
        return sorted(items, key=lambda x: (not x[1], x[0].name.lower()))
    
    def _filter_items(self):
        """Filter items based on search text."""
        if not self.search_text:
            self.filtered_items = self.items
        else:
            search_terms = self.search_text.lower().split()
            self.filtered_items = [
                item for item in self.items
                if all(term in item[0].name.lower() for term in search_terms)
            ]
        self.selected_index = min(self.selected_index, len(self.filtered_items) - 1)
        self.selected_index = max(0, self.selected_index)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Path]:
        """Handle input events. Returns selected file path if confirmed."""
        if event.type == pygame.KEYDOWN:
            if self.search_active:
                if event.key == pygame.K_RETURN:
                    self.search_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.search_text = self.search_text[:-1]
                    self._filter_items()
                elif event.key == pygame.K_ESCAPE:
                    self.search_active = False
                elif event.unicode.isprintable():
                    self.search_text += event.unicode
                    self._filter_items()
            else:
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.filtered_items) - 1, self.selected_index + 1)
                elif event.key == pygame.K_RETURN:
                    if self.filtered_items:
                        selected_item = self.filtered_items[self.selected_index]
                        if selected_item[1]:  # If it's a directory
                            self.base_path = selected_item[0]
                            self.items = self._scan_directory(self.base_path)
                            self.filtered_items = self.items
                            self.selected_index = 0
                            self.search_text = ""
                        else:  # If it's a file
                            return selected_item[0]
                elif event.key == pygame.K_BACKSPACE and not self.search_active:
                    if self.base_path.parent.name == "songs":
                        return None
                    self.base_path = self.base_path.parent
                    self.items = self._scan_directory(self.base_path)
                    self.filtered_items = self.items
                    self.selected_index = 0
                elif event.key == pygame.K_SLASH:
                    self.search_active = True
                elif event.key == pygame.K_f:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        pygame.display.set_mode((pygame.display.Info().current_w, pygame.display.Info().current_h), pygame.FULLSCREEN)
                    else:
                        pygame.display.set_mode((int(pygame.display.Info().current_w * 0.8), int(pygame.display.Info().current_h * 0.8)))
        
        return None
    
    def _setup_display(self, surface: pygame.Surface):
        """Adjust UI elements based on current surface size."""
        self.width = surface.get_width()
        self.height = surface.get_height()
        
        # Recalculate UI parameters based on new dimensions
        self.padding = int(self.width * 0.02)  # 2% of width
        self.item_height = int(self.height * 0.05)  # 5% of height
        self.search_height = int(self.height * 0.06)  # 6% of height
        self.visible_items = min(15, int((self.height - self.search_height - self.padding * 4) / self.item_height))

    def draw(self, surface: pygame.Surface):
        """Draw the song selector UI."""
        self._setup_display(surface)
        
        # Draw search bar
        search_rect = pygame.Rect(self.padding, self.padding, 
                                self.width - 2 * self.padding, self.search_height)
        pygame.draw.rect(surface, self.search_color, search_rect, 2)
        
        # Draw search text or placeholder
        if self.search_active:
            # Update cursor visibility every 500ms
            if pygame.time.get_ticks() - self.cursor_timer > 500:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = pygame.time.get_ticks()
            
            display_text = self.search_text + ('|' if self.cursor_visible else '')
        else:
            display_text = self.search_text or "Press '/' to search..."
        
        text_surface = self.font.render(display_text, True, self.text_color)
        surface.blit(text_surface, (search_rect.x + 10, search_rect.y + 10))
        
        # Draw current directory path
        path_text = f"Current directory: {self.base_path}"
        path_surface = self.small_font.render(path_text, True, self.text_color)
        surface.blit(path_surface, (self.padding, search_rect.bottom + 10))
        
        # Calculate visible items
        start_y = search_rect.bottom + 40
        visible_area_height = self.height - start_y - self.padding
        max_visible = min(len(self.filtered_items), int(visible_area_height / self.item_height))
        
        # Ensure selected item is visible
        if self.selected_index < self.scroll_position:
            self.scroll_position = self.selected_index
        elif self.selected_index >= self.scroll_position + max_visible:
            self.scroll_position = self.selected_index - max_visible + 1
        
        # Draw items
        for i in range(max_visible):
            idx = i + self.scroll_position
            if idx >= len(self.filtered_items):
                break
            
            item_path, is_dir = self.filtered_items[idx]
            item_name = item_path.name
            if is_dir:
                item_name = f"📁 {item_name}"
            
            # Draw selection highlight
            if idx == self.selected_index:
                highlight_rect = pygame.Rect(self.padding, start_y + i * self.item_height,
                                          self.width - 2 * self.padding, self.item_height)
                pygame.draw.rect(surface, self.selected_color, highlight_rect)
            
            # Draw item text
            text_surface = self.font.render(item_name, True, self.text_color)
            surface.blit(text_surface, (self.padding + 10, start_y + i * self.item_height + 5))

def main():
    pygame.init()
    pygame.display.set_caption("Music Visualizer")
    
    # Set up the display
    info = pygame.display.Info()
    width = info.current_w
    height = info.current_h
    fullscreen = True
    
    if fullscreen:
        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((int(width * 0.8), int(height * 0.8)))
    
    # Check command line arguments
    if len(sys.argv) == 2:
        audio_path = Path(sys.argv[1])
        if audio_path.is_file():
            visualizer = AudioVisualizer(width, height)
            visualizer.load_audio(str(audio_path))
            visualizer.run(str(audio_path))
        elif audio_path.is_dir():
            selector = SongSelector(width, height)
            selector.base_path = audio_path
            selector.items = selector._scan_directory(audio_path)
            selector.filtered_items = selector.items
        else:
            print(f"Error: {audio_path} not found")
            return
    else:
        selector = SongSelector(width, height)
    
    # Main selection loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        screen.fill((30, 30, 30))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if fullscreen:
                        fullscreen = False
                        screen = pygame.display.set_mode((int(width * 0.8), int(height * 0.8)))
                        selector._setup_display(screen)
                    else:
                        running = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((int(width * 0.8), int(height * 0.8)))
                    selector._setup_display(screen)
                else:
                    selected_path = selector.handle_event(event)
                    if selected_path:
                        visualizer = AudioVisualizer(width, height)
                        visualizer.fullscreen = fullscreen  # Sync fullscreen state
                        visualizer.load_audio(str(selected_path))
                        visualizer.run(str(selected_path))
                        # After visualizer exits, restore the selector screen
                        if fullscreen:
                            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((int(width * 0.8), int(height * 0.8)))
                        pygame.display.set_caption("Music Visualizer")
                        selector._setup_display(screen)
        
        selector.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    import sys
    main()
