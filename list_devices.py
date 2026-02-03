import pyaudio

def test_samplerate_on_devices():
    p = pyaudio.PyAudio()
    print("\n--- Searching for a device that supports 16000Hz ---")
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    
    target_rate = 16000
    
    for i in range(0, num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        name = device_info.get('name')
        max_in = device_info.get('maxInputChannels')
        
        if max_in > 0:
            print(f"Index {i}: {name}")
            try:
                supported = p.is_format_supported(
                    rate=target_rate,
                    input_device=i,
                    input_channels=1,
                    input_format=pyaudio.paInt16
                )
                print(f"  [SUCCESS] Supports {target_rate}Hz natively or via ALSA plugin.")
            except Exception as e:
                print(f"  [FAILED] Does not support {target_rate}Hz: {e}")
            print("-" * 30)
            
    p.terminate()

if __name__ == "__main__":
    test_samplerate_on_devices()
