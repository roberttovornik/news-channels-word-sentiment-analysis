import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import shutil
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet, stopwords
from nltk.tokenize import RegexpTokenizer, word_tokenize
from nltk import pos_tag
import xml.etree.ElementTree as ET
from lxml import etree
from collections import Counter
import re

appos = {
"aren't" : "are not",
"can't" : "cannot",
"couldn't" : "could not",
"didn't" : "did not",
"doesn't" : "does not",
"don't" : "do not",
"hadn't" : "had not",
"hasn't" : "has not",
"haven't" : "have not",
"he'd" : "he would",
"he'll" : "he will",
"he's" : "he is",
"i'd" : "I would",
"i'd" : "I had",
"i'll" : "I will",
"i'm" : "I am",
"isn't" : "is not",
"it's" : "it is",
"it'll":"it will",
"i've" : "I have",
"let's" : "let us",
"mightn't" : "might not",
"mustn't" : "must not",
"shan't" : "shall not",
"she'd" : "she would",
"she'll" : "she will",
"she's" : "she is",
"shouldn't" : "should not",
"that's" : "that is",
"there's" : "there is",
"they'd" : "they would",
"they'll" : "they will",
"they're" : "they are",
"they've" : "they have",
"we'd" : "we would",
"we're" : "we are",
"weren't" : "were not",
"we've" : "we have",
"what'll" : "what will",
"what're" : "what are",
"what's" : "what is",
"what've" : "what have",
"where's" : "where is",
"who'd" : "who would",
"who'll" : "who will",
"who're" : "who are",
"who's" : "who is",
"who've" : "who have",
"won't" : "will not",
"wouldn't" : "would not",
"you'd" : "you would",
"you'll" : "you will",
"you're" : "you are",
"you've" : "you have",
"'re": " are",
"wasn't": "was not",
"we'll":" will",
"didn't": "did not"
}

slo_stopwords = ["a","ali","april","avgust","b","bi","bil","bila","bile","bili","bilo","biti","blizu","bo","bodo","bojo","bolj","bom","bomo","boste","bova","boš","brez","c","cel","cela","celi","celo","d","da","daleč","dan","danes","datum","december","deset","deseta","deseti","deseto","devet","deveta","deveti","deveto","do","dober","dobra","dobri","dobro","dokler","dol","dolg","dolga","dolgi","dovolj","drug","druga","drugi","drugo","dva","dve","e","eden","en","ena","ene","eni","enkrat","eno","etc.","f","februar","g","g.","ga","ga.","gor","gospa","gospod","h","halo","i","idr.","ii","iii","in","iv","ix","iz","j","januar","jaz","je","ji","jih","jim","jo","julij","junij","jutri","k","kadarkoli","kaj","kajti","kako","kakor","kamor","kamorkoli","kar","karkoli","katerikoli","kdaj","kdo","kdorkoli","ker","ki","kje","kjer","kjerkoli","ko","koder","koderkoli","koga","komu","kot","kratek","kratka","kratke","kratki","l","lahka","lahke","lahki","lahko","le","lep","lepa","lepe","lepi","lepo","leto","m","maj","majhen","majhna","majhni","malce","malo","manj","marec","me","med","medtem","mene","mesec","mi","midva","midve","mnogo","moj","moja","moje","mora","morajo","moram","moramo","morate","moraš","morem","mu","n","na","nad","naj","najina","najino","najmanj","naju","največ","nam","narobe","nas","nato","nazaj","naš","naša","naše","ne","nedavno","nedelja","nek","neka","nekaj","nekatere","nekateri","nekatero","nekdo","neke","nekega","neki","nekje","neko","nekoga","nekoč","ni","nikamor","nikdar","nikjer","nikoli","nič","nje","njega","njegov","njegova","njegovo","njej","njemu","njen","njena","njeno","nji","njih","njihov","njihova","njihovo","njiju","njim","njo","njun","njuna","njuno","no","nocoj","november","npr.","o","ob","oba","obe","oboje","od","odprt","odprta","odprti","okoli","oktober","on","onadva","one","oni","onidve","osem","osma","osmi","osmo","oz.","p","pa","pet","peta","petek","peti","peto","po","pod","pogosto","poleg","poln","polna","polni","polno","ponavadi","ponedeljek","ponovno","potem","povsod","pozdravljen","pozdravljeni","prav","prava","prave","pravi","pravo","prazen","prazna","prazno","prbl.","precej","pred","prej","preko","pri","pribl.","približno","primer","pripravljen","pripravljena","pripravljeni","proti","prva","prvi","prvo","r","ravno","redko","res","reč","s","saj","sam","sama","same","sami","samo","se","sebe","sebi","sedaj","sedem","sedma","sedmi","sedmo","sem","september","seveda","si","sicer","skoraj","skozi","slab","smo","so","sobota","spet","sreda","srednja","srednji","sta","ste","stran","stvar","sva","t","ta","tak","taka","take","taki","tako","takoj","tam","te","tebe","tebi","tega","težak","težka","težki","težko","ti","tista","tiste","tisti","tisto","tj.","tja","to","toda","torek","tretja","tretje","tretji","tri","tu","tudi","tukaj","tvoj","tvoja","tvoje","u","v","vaju","vam","vas","vaš","vaša","vaše","ve","vedno","velik","velika","veliki","veliko","vendar","ves","več","vi","vidva","vii","viii","visok","visoka","visoke","visoki","vsa","vsaj","vsak","vsaka","vsakdo","vsake","vsaki","vsakomur","vse","vsega","vsi","vso","včasih","včeraj","x","z","za","zadaj","zadnji","zakaj","zaprta","zaprti","zaprto","zdaj","zelo","zunaj","č","če","često","četrta","četrtek","četrti","četrto","čez","čigav","š","šest","šesta","šesti","šesto","štiri","ž","že"]


def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return wordnet.VERB
    elif treebank_tag.startswith('N'):
        return wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return wordnet.ADV
    else:
        #return wordnet.NOUN
        return '_'

def extract_pos_constructs(obeliks_xml):
    root = ET.fromstring(obeliks_xml)
    stavki = root.findall(".//{http://www.tei-c.org/ns/1.0}s")
    stavcne_strukture = []
    #besedilo_tokens = Counter()
    lemmatized_article=[]
    pos_tagged_article=[]

    for stavek in stavki:
        stavcna_struktura = ''
        lemmatized_sentence = [x.attrib['lemma'] if 'lemma' in x.attrib else '_' for x in stavek ]
        lemmatized_article = lemmatized_article + lemmatized_sentence
        pos_tagged_sentence = [x.attrib['msd'] if 'msd' in x.attrib else '_' for x in stavek]
        pos_tagged_article = pos_tagged_article + pos_tagged_sentence
    return (' '.join(lemmatized_article),' '.join(pos_tagged_article))


def lemmatize_slovenian(article_iterator):
    input_article_directory_name = '.articles/'
    output_article_directory_name = '.articles_tagged/'
    if os.path.exists(input_article_directory_name) and os.path.isdir(input_article_directory_name):
        shutil.rmtree(input_article_directory_name)
    if os.path.exists(output_article_directory_name) and os.path.isdir(output_article_directory_name):
        shutil.rmtree(output_article_directory_name)    
    os.makedirs(input_article_directory_name, exist_ok=True)
    os.makedirs(output_article_directory_name, exist_ok=True)
    latest_processed_file = max([int(f[1:f.index('.out')]) for f in os.listdir(output_article_directory_name)]) if len(os.listdir(output_article_directory_name)) > 0 else None
    for idx,article in article_iterator.iteritems():
        if latest_processed_file and idx <= latest_processed_file:
            continue
        with open(input_article_directory_name + str(idx) + '.txt', 'w') as file:
            file.write(article)
    #sudo apt install mono-devel
    os.system('exec mono obeliks/PosTaggerTag.exe -lem:obeliks/LemmatizerModel.bin -v -o -t "' + input_article_directory_name + '*" obeliks/TaggerModel.bin ' + output_article_directory_name)
    output_article_directory = os.fsencode(output_article_directory_name)
    data_content_lemma = []
    data_content_pos = []
    data_indices=[]
    for file in os.listdir(output_article_directory):
        filename = os.fsdecode(file)
        with open(output_article_directory_name + filename, 'r') as the_file:
            content = the_file.read()
            lemmatized_string,pos_string=extract_pos_constructs(content)
        idx = int(filename[1:filename.find('.out')])
        data_indices.append(idx)
        data_content_lemma.append(lemmatized_string)
        data_content_pos.append(pos_string)

    return (pd.Series(data=data_content_lemma,index=data_indices),pd.Series(data=data_content_pos,index=data_indices))

def lemmatize_english(article_iterator):
    wordnet_lemmatizer = WordNetLemmatizer()
    tokenizer = RegexpTokenizer(r'\w+')
    #data_lemmatized=article_iterator.apply(lambda a:' '.join([wordnet_lemmatizer.lemmatize(word,pos=get_wordnet_pos(tag) if not get_wordnet_pos(tag) == '_' else  wordnet.NOUN) for word,tag in pos_tag(tokenizer.tokenize(a))]) if not isinstance(a, float) else a)

    data_content_lemma = []
    data_content_pos = []
    data_indices = []

    for idx,content in article_iterator.iteritems():
        data_indices.append(idx)
        content_pos_tmp = []
        content_lemma_tmp = []
        if isinstance(content, float):
            data_content_lemma.append(content)
            data_content_pos.append(content)
            continue
        else:
            tokens=tokenizer.tokenize(content)
            for word,tag in pos_tag(tokens):
                lemma=wordnet_lemmatizer.lemmatize(word,pos=get_wordnet_pos(tag) if not get_wordnet_pos(tag) == '_' else  wordnet.NOUN)
                content_pos_tmp.append(str(tag))
                content_lemma_tmp.append(lemma)
        data_content_lemma.append(' '.join(content_lemma_tmp))
        data_content_pos.append(' '.join(content_pos_tmp))

    return (pd.Series(data=data_content_lemma,index=data_indices),pd.Series(data=data_content_pos,index=data_indices))

def basic_preprocessing(article, region=None):
    if not isinstance(article, float):
        print(" UNPROCESSED ")
        print("================================================================")
        print(article)

        article = article.lower()  # normalization - easier filtering

        if region != "Slovenia":
            # list https://drive.google.com/file/d/0B1yuv8YaUVlZZ1RzMFJmc1ZsQmM/view
            words = article.split()
            reformed = [appos[word] if word in appos else word for word in words]
            article = " ".join(reformed)

        # remove url links, tweets, etc HERE .. 
        article = re.sub(r"http\S+", "", article)

        # remove redundant chars
        article = article.replace('\n', ' ').replace('\r', '') # eliminate any remaining newlines
        article = re.sub(r'[^\w\s]','', article)   # remove any punctuations, special chars

        # simple tokenization and remove stopwords 
        if region != "Slovenia":
            tokens = word_tokenize(article)
            stop_words = stopwords.words('english')
        else:
            tokens = article.split()
            stop_words = slo_stopwords


        stop_stripped = [word for word in tokens if word not in stop_words] # remove stopwords
        num_stripped = [word for word in stop_stripped if word.isalpha() ]  # remove numbers

        article = " ".join(num_stripped)
        
        print("----------------------------------------------------------")
        print(article)
        print("================================================================================")


    return article


geoRegional_data_dir_paths={'UK':['../../corpus/scrapers/bbc-co-uk/'],
                  'Slovenia':['../../corpus/scrapers/rtv/'],
                  'USA':['../../corpus/scrapers/pbs/'],
                  'Middle East':['../../corpus/scrapers/al-jazeera/'],
                  'Austria':['../../corpus/scrapers/the-local/austria/'],
                  'Denmark':['../../corpus/scrapers/the-local/denmark/'],
                  'Germany':['../../corpus/scrapers/the-local/germany/'],
                  'Italy':['../../corpus/scrapers/the-local/italy/'],
                  'Norway':['../../corpus/scrapers/the-local/norway/'],
                  'Spain':['../../corpus/scrapers/the-local/spain/'],
                  'Sweden':['../../corpus/scrapers/the-local/sweden/'],
                  'Switzerland':['../../corpus/scrapers/the-local/switzerland/'],
                  'other':['../../corpus/scrapers/positive-news']}
geoRegional_data={}

#========== LOAD DATA ==========
print('***Loading data...')
for region,data_dirs in geoRegional_data_dir_paths.items():
    data_csv_paths=[]
    for dir in data_dirs:
        for (dirpath, dirnames, filenames) in os.walk(dir):
            data_csv_paths+=[dirpath+'/'+f for f in filenames if '.csv' in f]
    dataframes=[]
    for dir in data_csv_paths:
        df = pd.read_csv(dir)
        dataframes.append(df)
    geoRegional_data[region]=pd.concat(dataframes)
print('...data loaded.')
#========== GET SOME INFO ABOUT RAW DATA ==========
print('\n***Inspecting raw data...')
article_word_count_distribution_df={}
article_word_count_distribution_unique_df={}
print('\nData info by region:')
for region,data in geoRegional_data.items():
    #How many articles?
    nr_articles=data.shape[0]
    articles_word_split=[a.split() for a in data['article_text'] if not isinstance(a, float)]
    # How many words per article?
    articles_word_count=[len(a) for a in articles_word_split]
    article_word_count_distribution_df[region]=articles_word_count
    mean_article_word_count=np.mean(articles_word_count)
    median_article_word_count=np.median(articles_word_count)
    #How many unique words per article?
    articles_word_count_unique=[len(set(a)) for a in articles_word_split]
    article_word_count_distribution_unique_df[region] = articles_word_count_unique
    mean_article_word_count_unique = np.mean(articles_word_count_unique)
    median_article_word_count_unique = np.median(articles_word_count_unique)
    print('\t' + region + ':')
    print('\t\tnumber of articles:',nr_articles)
    print('\t\tmean article word count:', mean_article_word_count)
    print('\t\tmedian article word count:', median_article_word_count)
    print('\t\tmean article unique word count:', mean_article_word_count_unique)
    print('\t\tmedian article unique word count:', median_article_word_count_unique)
article_word_count_distribution_df=pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in article_word_count_distribution_df.items() ]))
article_word_count_distribution_unique_df=pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in article_word_count_distribution_unique_df.items() ]))

ax = sns.boxplot(data=article_word_count_distribution_df, orient='h')
ax.set(xlabel='stevilo besed')
plt.savefig('../../HISTOGRAM_article_wordCount_raw.png', bbox_inches='tight')
plt.close()
ax = sns.boxplot(data=article_word_count_distribution_unique_df, orient='h')
ax.set(xlabel='stevilo unikatnih besed')
plt.savefig('../../HISTOGRAM_article_uniqueWordCount_raw.png', bbox_inches='tight')
plt.close()
print('...done.')
#========== PROCESS DATA ==========
counter = 0
n = 3
print('\n***Processing data...')
for region,df in geoRegional_data.items():
    counter += 1
    print('\tProcessing articles for region:',region)
    print('\t\tApplying basic pre-processing..')
    df['article_text_processed']=df['article_text'].apply(basic_preprocessing, region=region)
    print('\t\t...done.')

    if counter > n:
        exit()
    continue
    
    print('\t\tPOS tagging and lemmatization...')
    if region=='Slovenia':
        #df=df.copy(deep=True)[:5]
        df['article_text_processed_lemmatized'], df['article_text_processed_POS'] = lemmatize_slovenian(df['article_text_processed'].copy(deep=True))
    else:
        df['article_text_processed_lemmatized'], df['article_text_processed_POS'] = lemmatize_english(df['article_text_processed'].copy(deep=True))
    print('\t\t...done.')
    df_save_file_path='../data/'+region+'.pkl'
    print('\t\tSaving dataframe to:',df_save_file_path)
    df.to_pickle(df_save_file_path)
    print('\t\t...done.')
print('...data processed.')