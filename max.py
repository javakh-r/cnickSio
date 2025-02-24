import pygame
import time

# Initialize pygame mixer
pygame.mixer.init()

# Load and play the audio file
def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():  # Wait for the music to finish playing
        time.sleep(0.1)

if __name__ == "__main__":
    audio_file = "test.wav"  # Replace with your audio file path
    print("Playing audio...")
    play_audio(audio_file)
    print("Playback finished.")
