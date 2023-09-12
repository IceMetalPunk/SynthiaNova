import os
from dotenv import load_dotenv
load_dotenv()
from synthianova import SynthiaNova

if __name__ == '__main__':
    apiKey = os.getenv('OPENAI_KEY')
    synthia = SynthiaNova(apiKey)

    print('Synthia Nova is writing a new song... Please don\'t interrupt her writing process...')
    songtitle = synthia.write_song()
    print(f'Synthia has written a new song, called "{songtitle}"! Just giving it a proofread now...')
    synthia.process_songs()
    synthia.save_songs()
    print('Done and saved!')