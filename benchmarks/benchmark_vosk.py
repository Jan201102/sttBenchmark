import os 
from vosk import Model, KaldiRecognizer, SetLogLevel
import time
import wave
import pandas as pd
import json


#load list of wav files
wav_files = os.listdir('./wavStore/')
wav_files = [f for f in wav_files if f.endswith('.wav')]
transcripts = pd.DataFrame(columns=['file_name', 'transcript','duration'])
model_name = "vosk-model-small-de-0.15"  # Path to the Vosk model
num_wav_files = len(wav_files)

# Initialize the Vosk model
SetLogLevel(-1)  # Suppress Vosk logs
vosk_model = Model(model_name = model_name)
rec = KaldiRecognizer(vosk_model, 16000)
rec.SetWords(True)  # Enable word-level timestamps
rec.SetPartialWords(True)  # Enable partial words

for i,wav_file in enumerate(wav_files):
    wf = wave.open(f'./wavStore/{wav_file}', "rb")
    start_time = time.perf_counter()
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    result = json.loads(rec.FinalResult())
    wf.close()
    end_time = time.perf_counter()
    duration = end_time - start_time

    transcripts = pd.concat([transcripts,
                             pd.DataFrame({
                                'file_name': [wav_file],
                                'transcript': [result['text']],
                                'duration': [duration]
                            })], ignore_index=True)
    print(f'Processed {i+1}/{num_wav_files}')
# Save the transcripts to a CSV file
transcripts.to_csv(f'./transcripts_{model_name}.csv', index=False)


