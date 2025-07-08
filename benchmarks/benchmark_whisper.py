import os 
import whisper
import time
import pandas as pd


#load list of wav files
wav_files = os.listdir('./wavStore/')
wav_files = [f for f in wav_files if f.endswith('.wav')]
transcripts = pd.DataFrame(columns=['file_name', 'transcript','duration'])
model_name = "medium"
model = whisper.load_model(model_name)
num_wav_files = len(wav_files)
for i,wav_file in enumerate(wav_files):
    start_time = time.perf_counter()
    result = model.transcribe(f'./wavStore/{wav_file}')
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


