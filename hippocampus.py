from sentence_transformers import SentenceTransformer, CrossEncoder, util
import faiss
import re
import json
import os
model = SentenceTransformer('multi-qa-MiniLM-L6-cos-v1')
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

class Memories:
    memory_list = list()
    database = None
    name = None
    memory_embeddings = None
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
        self.memory_embeddings = model.encode(self.memory_list, convert_to_tensor=True)
        index = faiss.IndexFlatL2(self.memory_embeddings.shape[1])
        index.add(self.memory_embeddings)
        
        faiss.write_index(index, 'index_' + self.getCleanName() + '_memories')
        self.database = faiss.read_index('index_'+self.getCleanName()+'_memories')

    def recall(self, query: str):
        if len(self.memory_list) <= 0 or self.database is None:
            return []
        ''' Note: Will only search through the last saved memories, so save before searching! '''
        query_vector = model.encode(query, convert_to_tensor=True)
        k = min(5, len(self.memory_list)) # Top 5 max; feel free to change this as needed
        
        retrieve = min(k * 7, len(self.memory_list))
        matches = util.semantic_search(query_embeddings=query_vector, corpus_embeddings=self.memory_embeddings, top_k=retrieve)
        matches = matches[0]

        cross_matches = [[query, self.memory_list[match['corpus_id']]] for match in matches]
        cross_scores = cross_encoder.predict(cross_matches)
        for idx in range(len(cross_scores)):
            matches[idx]['cross-score'] = cross_scores[idx]
            matches[idx]['text'] = self.memory_list[matches[idx]['corpus_id']]
        matches = sorted(matches, key=lambda x: x['cross-score'], reverse=True)

        # The 2 here is a "magic number", a threshold for how relevant, compared to the top result, the other memories must be to be recalled
        matches = [x['text'] for x in matches[0:k] if matches[0]['cross-score'] - x['cross-score'] < 2]
        return matches