# Synthia Nova
### An AI songwriter with personality

#### Installation
First, clone the repo into an empty directory and install the Python requirements:
```bash
mkdir synthia_nova
cd synthia_nova
git clone https://github.com/IceMetalPunk/SynthiaNova.git .
pip install -r requirements.txt
```

Then make sure you have an [OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key). The easiest way to use it is to put it in a `.env` file and then follow the `synthianova_example.py` code to see how to load the key. That `.env` file would look something like this:
```ini
OPENAI_KEY=<OpenAI_Key_Goes_Here>
```

(The `.env` file is already included in this repo's `.gitignore`, so if you do this, you can fork the repo and not worry about your OpenAI API key leaking.)

#### Usage
Check the `synthianova_example.py` file to see an example usage. But here's the basics:
1. Import the SynthiaNova class from `synthianova.py`.
2. Initialize an instance of the class, passing in your API key. You may optionally also pass the filename of the JSON file that songs will be saved to (default is just `songs.json`). If that file already exists, all songs will automatically be loaded from it into memory.
3. You can call `SynthiaNova.set_model(model)` to change the GPT model used. It defaults to `gpt-4-0613`. **NOTE:** It *must* be a model that supports Function Calling! Check the OpenAI documentation on Function Calling to see which ones qualify. Using an invalid model will not work.
4. Call `SynthiaNova.write_song()` to generate a new song. This will return the title of the song when it's done, and store the rest of the song info in memory. The AI is encouraged to generate songs that are different from all previously generated songs in memory.
4. After generating as many songs as you want, you can call `SynthiaNove.process_songs()` to enforce proper formatting on all songs. This means tagging verses vs chorus, ensuring final punctuation is followed by line breaks, and ensuring each section is broken into quatrain stanzas as best as possible.
5. You can call `SynthiaNova.get_songs()` to get the full dict of all songs in memory. But more likely, you'll want to call `SynthiaNova.save_songs()`, which will save all songs in memory to the JSON file you initialized the class with. *This will overwrite that file if it exists, but since SynthiaNova auto-loads existing songs on init, you shouldn't lose any songs from this process.*

#### Use with Suno Chirp
This framework was designed with [Suno Chirp](https://suno.ai) in mind. You should be able to copy/paste the song genre/style (with an added "female vocals" specified, if needed) directly into Chirp, and you should also be able to copy the lyrics in one stanza at a time (or more; that's your preference).

Really, copying the text into Chirp and curating the clips it generates should be the only human input needed to get great, original songs, written by Synthia Nova and performed by Chirp.

#### Modifying Synthia Nova
I encourage anyone to feel free to modify the prompts in the SynthiaNova class to suit your needs, or to experiment. There is only one thing I insist on if you do so: *Do not call your version Synthia Nova!* The name "Synthia Nova" refers to this original framework, and also to the personality this framework tries to keep consistent via its GPT prompt engineering. You can call your modified version anything else.

#### Usage/Cost Notes
Obviously, this will use your GPT account, and you will incur any costs from that accordingly. One important note is that, because the prompt for each new song includes an injected list of *all* previous song topics (to encourage variety), the more songs you generate, the more tokens you will use for each generation, thus technically costing you more.

That said, the subject strings are intentionally kept short, and in all my testing I've use less than $2, so it shouldn't be too bad compared to your usual ChatGPT / GPT API usage.