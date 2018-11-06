import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import shutil
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.tokenize import RegexpTokenizer
from nltk import pos_tag

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
        return wordnet.NOUN

def lemmatize_slovenian(article_iterator):
    input_article_directory_name = '.articles/'
    output_article_directory_name = '.articles_tagged/'
    '''
    if os.path.exists(input_article_directory_name) and os.path.isdir(input_article_directory_name):
        shutil.rmtree(input_article_directory_name)
    if os.path.exists(output_article_directory_name) and os.path.isdir(output_article_directory_name):
        shutil.rmtree(output_article_directory_name)    
    '''
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
    data_content=[]
    data_indices=[]
    for file in os.listdir(output_article_directory):
        filename = os.fsdecode(file)
        with open(output_article_directory_name + filename, 'r') as the_file:
            content = the_file.read()
        idx = int(filename[1:filename.find('.out')])
        data_indices.append(idx)
        data_content.append(content)

    return pd.Series(data=data_content,index=data_indices)

def lemmatize_english(article_iterator):
    wordnet_lemmatizer = WordNetLemmatizer()
    tokenizer = RegexpTokenizer(r'\w+')
    data_lemmatized=article_iterator.apply(lambda a:' '.join([wordnet_lemmatizer.lemmatize(word,pos=get_wordnet_pos(tag)) for word,tag in pos_tag(tokenizer.tokenize(a))]) if not isinstance(a, float) else a)
    return data_lemmatized

def basic_preprocessing(article):
    if not isinstance(article, float):
        article=article.lower()
        article=article.replace('"',' ')
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
                  'Switzerland':['../../corpus/scrapers/the-local/switzerland/']}
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
print('\n***Processing data...')
for region,df in geoRegional_data.items():
    print('\tProcessing articles for region:',region)
    print('\t\tApplying basic pre-processing..')
    df['article_text_processed']=df['article_text'].apply(basic_preprocessing)
    print('\t\t...done.')
    print('\t\tPOS tagging and lemmatization...')
    if region=='Slovenia':
        geoRegional_data[region]['article_text_processed_lemmatized']=lemmatize_slovenian(df['article_text_processed'])
    else:
        geoRegional_data[region]['article_text_processed_lemmatized'] = lemmatize_english(df['article_text_processed'])
    print('\t\t...done.')
    df_save_file_path='../data/'+region+'.pkl'
    print('\t\tSaving dataframe to:',df_save_file_path)
    df.to_pickle(df_save_file_path)
    print('\t\t...done.')
print('...data processed.')