import pyaudio
import numpy as np

#playback
speaker_sample_rate = 44100
speaker_channels = 1
speaker_chunk_size = 1024
speaker_pa_format = pyaudio.paFloat32
speaker_np_format = np.float32

#recording

mic_sample_rate = 16000
mic_channels = 1
mic_prebuffer_seconds = 1
mic_pa_format = pyaudio.paInt16
mic_np_format = np.int16
mic_frame_duration_ms = 30
mic_frame_size = int(mic_sample_rate * (mic_frame_duration_ms / 1000))
mic_circular_buffer_size = mic_sample_rate * 1
mic_vad_mode = 3
mic_req_voiced_frames = 10 # required amount of audio frames for vad to trigger/untrigger
mic_req_unvoiced_frames = 20