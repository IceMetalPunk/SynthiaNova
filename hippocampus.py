from sentence_transformers import SentenceTransformer
import faiss
import re
import json
import os
model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')

class Memories:
    memory_list = list()
    database = None
    name = None
    def __init__(self, name: str = 'Synthia Nova'):
        self.name = name
    def add(self, memory: str):
        ''' Note: ALWAYS remember to save after adding all your memories, or they won't be searchable! '''
        self.memory_list.append(memory)
    def getCleanName(self):
        return re.sub('[^a-zA-Z0-9_]', '_', self.name.lower())

    def load(self, filename: str = None):
        if filename is None:
            filename = self.getCleanName() + '_memories.json'
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write('[]')
        with open(filename, 'r') as f:
            self.memory_list = json.load(f)
        self.save(filename)

    def save(self, filename: str = None):
        if filename is None:
            filename = self.getCleanName() + '_memories.json'
        with open(filename, 'w') as f:
            json.dump(self.memory_list, f, indent = 2)
        if len(self.memory_list) <= 0:
            return
        embeddings = model.encode(self.memory_list)
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        
        faiss.write_index(index, 'index_' + self.getCleanName() + '_memories')
        self.database = faiss.read_index('index_'+self.getCleanName()+'_memories')

    def recall(self, query: str):
        if len(self.memory_list) <= 0 or self.database is None:
            return []
        ''' Note: Will only search through the last saved memories, so save before searching! '''
        query_vector = model.encode([query])
        k = 5 # Top 5 max; feel free to change this as needed
        top_k = self.database.search(query_vector, k)
        top_k_list = top_k[1].tolist()[0]
        # 0.1 is a magic number, obtained via a manual binary search for "good" results on real generated data; it might not be optimal
        # It's basically "how relevant must a memory be to be included in the results". Lower = more exact search, higher = more loose search.
        return [self.memory_list[_id] for ind, _id in enumerate(top_k_list) if _id >= 0 and abs(top_k[0][0][ind] - top_k[0][0][0]) < 0.1]