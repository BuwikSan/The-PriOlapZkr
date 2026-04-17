import numpy as np
from sympy import Matrix
CHARS = ["A", "Á", "B", "C", "Č", "D", "Ď", "E", "É", "Ě", "F", "G", "H", "I", "Í", "J", "K", "L", "M", "N", "Ň", "O", "Ó", "P", "Q", "R", "Ř", "S", "Š", "T", "Ť", "U", "Ú", "Ů", "V", "W", "X", "Y", "Ý", "Z", "Ž", " ", "."]
enumerated_characters = dict(enumerate(CHARS))
encharactered_numbers = {v: k for k, v in enumerated_characters.items()}


class Hills_cypher:
    CYPHER_ALPHABET = ["A", "Á", "B", "C", "Č", "D", "Ď", "E", "É", "Ě", "F", "G", "H", "I", "Í", "J", "K", "L", "M", "N", "Ň", "O", "Ó", "P", "Q", "R", "Ř", "S", "Š", "T", "Ť", "U", "Ú", "Ů", "V", "W", "X", "Y", "Ý", "Z", "Ž", " ", "."]
    CA_LEN = len(CYPHER_ALPHABET)
    enumerated_characters = dict(enumerate(CYPHER_ALPHABET))
    encharactered_numbers = {v: k for k, v in enumerated_characters.items()}

    def __init__(self, number_of_rounds=1, key_length=CA_LEN, rng_seed=None):
        self.rng = np.random.default_rng(rng_seed)
        self.rounds = number_of_rounds
        self.key_len = key_length
        self.keys = []
        self.inverse_keys = []
        self.padding_length = 0


    # key handling ------------------------------------------------------------------------------------
    def _generate_key(self):
        key_matrix = []
        for _ in range(self.key_len):
            key_matrix.append(self.rng.choice(list(range(self.key_len)), size=self.key_len, replace=True))
        return np.array(key_matrix)

    def _inverse_key_matrix(self, key_matrix):
        # Convert numpy array to sympy Matrix over integers mod 43
        matrix = Matrix(key_matrix.astype(int))
        try:
            # Compute inverse mod 43
            inv_matrix = matrix.inv_mod(self.CA_LEN)
            return np.array(inv_matrix)
        except ValueError as e:
            print(f"ERROR: Matrix is not invertible mod {self.CA_LEN}: {e}")
            raise

    def generate_new_set_of_keys(self):
        def matrix_generation(rounds):
            keys = []
            for _ in range(rounds):
                keys.append(self._generate_key())
            return keys

        if len(self.keys) > 0:
            if input("Keys are already generated, want to rewrite them? Y/N: ") == "Y":
                self.keys = matrix_generation(self.rounds)
                self.inverse_keys = [self._inverse_key_matrix(key) for key in self.keys]
            else:
                print("Keys already generated, aborting key generation.")
        else:
            self.keys = matrix_generation(self.rounds)
            self.inverse_keys = [self._inverse_key_matrix(key) for key in self.keys]


    # formatting and encoding -------------------------------------------------------------------------------
    def _text_number_transformation(self, vectors):
        dict = encharactered_numbers if isinstance(vectors[0][0], str) else enumerated_characters
        
        for i in range(len(vectors)):
            for j in range(len(vectors[i])):
                vectors[i][j] = dict[vectors[i][j]]
        return vectors

    def _text_preprocessing(self, text, decypher=False):
        def text_sanitization(text):
            text = text.upper()
            text = ''.join(filter(lambda x: x in CHARS, text))
            self.padding_length = (self.key_len - (len(text) % self.key_len))
            text = (text + "Q"*self.padding_length)
            return text

        if decypher == False:
            text = text_sanitization(text)

        text_number_vectors = []
        while text:
            text_number_vectors.append(list(text[:self.key_len]))
            text = text[self.key_len:]
        return np.array(self._text_number_transformation(text_number_vectors))


    # cyphering logic ---------------------------------------------------------------------------------------
    def _cyphering_logic(self, vectors, decypher=False):
        def cypher_operation(input_vector, key):
            new_vector = key.dot(input_vector)
            return new_vector % self.CA_LEN

        def cypher_round(input_vectors, key):
            new_vectors = []
            for vector in input_vectors:
                new_vectors.append(cypher_operation(vector, key))
            return np.array(new_vectors)
        
        for key in self.keys if not decypher else self.inverse_keys:
            vectors = cypher_round(vectors, key)

        new_vectors = []
        for vector in vectors:
            new_vectors.append(list(vector))

        final_vectors = self._text_number_transformation(new_vectors)
        final_string_stream = ""
        for i in range(len(final_vectors)):
            final_string_stream += "".join(final_vectors[i])
        if decypher:
            final_string_stream = final_string_stream[:-self.padding_length]
        return final_string_stream

    def cypher(self, text):
        vectors = self._text_preprocessing(text)
        return self._cyphering_logic(vectors)

    def decypher(self, text):
        vectors = self._text_preprocessing(text, decypher=True)
        return self._cyphering_logic(vectors, decypher=True)




def main(): 
    text = "V relačním modelu jsou data uložena v tabulkách, na které má jisté požadavky. Při splnění požadavků je tabulka označována jako normalizovaná. Pokud nejsou tyto požadavky splněny, jsou označovány jako nenormalizované a proces jejich převodu na tabulky se označuje jako normalizace. Při tomto procesu dochází k odstraňování nedostatků tabulek jako je redundance nebo možnost vzniku aktualizační anomálie, tj. nechtěného vedlejšího efektu operace nad databází, při kterém dojde ke ztrátě nebo nekonzistenci dat. Postup normalizace je rozdělen do několika kroků a po dokončení každého z nich se tabulka nachází v určité normální formě. V praxi se většinou normalizuje do třetí normální formy, vyšší normální formy je vcelku obtížné porušit a vyžadují relativně velké znalosti, stejně jako návrh databází takové velikosti, kde je možné je porušit."
    cypher_engine = Hills_cypher()
    cypher_engine.generate_new_set_of_keys()

    cyphered_text = cypher_engine.cypher(text)
    print(cyphered_text)
    decyphered_text = cypher_engine.decypher(cyphered_text)
    print(decyphered_text)
if __name__ == "__main__":
    main()