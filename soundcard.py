import simpleaudio as sa

# Load the WAV file
wave_obj = sa.WaveObject.from_wave_file("test.wav")

# Play the audio
play_obj = wave_obj.play()

# Wait until the audio finishes playing
play_obj.wait_done()
