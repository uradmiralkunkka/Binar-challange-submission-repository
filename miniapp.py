import re
import pandas as pd

from flask import Flask, jsonify

app = Flask(__name__)

from flask import request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from

df = pd.read_csv('data.csv', encoding='latin-1') #data that will be analyzed

alay_dictionary = pd.read_csv('new_kamusalay.csv', encoding='latin-1', header=None) #data "alay dictionary"
alay_dictionary = alay_dictionary.rename(columns={0: 'original', 
                                      1: 'replacement'}) 

d_abusive = pd.read_csv('abusive.csv', encoding='latin-1', header=None) #data abusive.
d_abusive = d_abusive.rename(columns={0: 'abusive'}) 

d_stopword1 = pd.read_csv('stopwordbahasa.csv', header=None) #data stop word.
d_stopword1 = d_stopword1.rename(columns={0: 'stopword'})
stopwords_new = pd.DataFrame(['sih','nya', 'iya', 'nih', 'biar', 'tau', 'kayak', 'banget'], columns=['stopword'])
d_stopword1 = pd.concat([d_stopword1,stopwords_new]).reset_index()
d_stopword1 = pd.DataFrame(d_stopword1['stopword'])


app.json_encoder = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Processing and Modeling'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi API untuk Data Processing dan Modeling'),
    },
    host = LazyString(lambda: request.host)
)
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}
swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)


# rules 1
def lowercase(text):
    return text.lower()

# rules 2
def remove_unnecessary_char(text):
    text = re.sub('\n',' ',text) # Remove '\n'
    text = re.sub('rt',' ',text) # Remove retweet symbol
    text = re.sub('user',' ',text) # Username omitted
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',text) # Remove URL
    text = re.sub('  +', ' ', text) # Extra spaces removed
    return text

# rules 3
def remove_nonaplhanumeric(text):
    text = re.sub('[^0-9a-zA-Z]+', ' ', text) 
    return text

# rules 4
alay_dict_map = dict(zip(alay_dictionary['original'], alay_dictionary['replacement']))
def normalize_alay(text):
    return ' '.join([alay_dict_map[word] if word in alay_dict_map else word for word in text.split(' ')])

# rules 5
def remove_abusive(text):
    text = ' '.join(['' if word in d_abusive.abusive.values else word for word in text.split(' ')])
    text = re.sub('  +', ' ', text) # Remove extra spaces
    text = text.strip()
    return text

# rules 6
def stopword_remover(text):
    text = ' '.join(['' if word in d_stopword1.stopword.values else word for word in text.split(' ')])
    text = re.sub('  +', ' ', text) # Remove extra spaces
    text = text.strip()
    return text

# all rules are merged into 1
def preprocess(text):
    text = lowercase(text) # 1 Replacing capital letters with lowercase letters
    text = remove_nonaplhanumeric(text) # 2 Removes all characters other than alphabets
    text = remove_unnecessary_char(text) # 3 Remove unnecessary characters
    text = normalize_alay(text) # 4 Eliminate "alay" words, and replace them with standard words.
    text = remove_abusive(text) # 5 Eliminate abusive words
    text = stopword_remover(text) # 6 Remove stopwords in tweets
    return text

@swag_from("docs/landingpage.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code': 200,
        'description': "Development of Mini Application of Indonesian Abusive Words Filter on Twitter with Descriptive Methods.",
        'data': "Binar Academy - Febrian Nur Alam - DSC 7",
    }

    response_data = jsonify(json_response)
    return response_data

# The first endpoint of the input form cleanup
@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():

    text = request.form.get('text')

    json_response = {
        'status_code': 200,
        'description': "Teks yang sudah diproses",
        # 'data': re.sub(r'[^a-zA-Z0-9]', ' ', text),
        'data' : preprocess(text)
    }

    response_data = jsonify(json_response)
    return response_data

# second endpoint cleansing of files
@swag_from("docs/text_processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():

    # Upladed file
    file = request.files.getlist('file')[0]

    # Import file csv ke Pandas
    df = pd.read_csv(file, encoding='latin-1')


    # Do a text cleansing
    cleaned_text = []
    for text in df['Tweet']:


        cleaned_text.append(preprocess(text))

    df['cleaned_text'] = cleaned_text

    json_response = {
        'status_code': 200,
        'description': "Processed texts",
        'data': cleaned_text
    }

    response_data = jsonify(json_response)
    return response_data

if __name__ == '__main__':
   app.run()