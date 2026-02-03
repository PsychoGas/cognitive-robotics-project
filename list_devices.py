import pyaudio

def test_all_devices():
    p = pyaudio.PyAudio()
    print("\n--- Checking ALL devices for 16kHz Input Support ---")
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info.get('name')
        max_in = info.get('maxInputChannels')
        
        # We check every device that has at least 1 input channel
        if max_in >= 1:
            print(f"Index {i}: {name} (Channels: {max_in})")
            try:
                # Check for mono (1 channel) at 16000Hz
                # Porcupine requires specifically mono 16kHz
                if p.is_format_supported(16000, input_device=i, input_channels=1, input_format=pyaudio.paInt16):
                    print(f"  [SUCCESS] Supports 16000Hz (Mono)!")
                else:
                    print(f"  [FAILED] is_format_supported returned False.")
            except Exception as e:
                # Check if maybe it supports it via stereo if mono fails
                try:
                    if p.is_format_supported(16000, input_device=i, input_channels=2, input_format=pyaudio.paInt16):
                         print(f"  [HALF-SUCCESS] Supports 16000Hz but ONLY in Stereo (2 channels).")
                    else:
                         print(f"  [FAILED] 16000Hz not supported (tried Mono/Stereo): {e}")
                except:
                    print(f"  [FAILED] 16000Hz not supported: {e}")
            print("-" * 30)
            
    p.terminate()

if __name__ == "__main__":
    test_all_devices()
