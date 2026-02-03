import pyaudio

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("\n--- Available Audio Input Devices ---")
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    
    for i in range(0, num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"Index {i}: {device_info.get('name')}")
            print(f"  Max Input Channels: {device_info.get('maxInputChannels')}")
            print(f"  Default Sample Rate: {device_info.get('defaultSampleRate')}")
            print("-" * 30)
    
    print("\n--- Available Audio Output Devices ---")
    for i in range(0, num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxOutputChannels') > 0:
            print(f"Index {i}: {device_info.get('name')}")
            print(f"  Max Output Channels: {device_info.get('maxOutputChannels')}")
            print("-" * 30)
            
    p.terminate()

if __name__ == "__main__":
    list_audio_devices()
