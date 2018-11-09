import os
import gensim
import pandas as pd


def list_word_pos(df):
    word_pos_tags={}
    for idx,row in df.iterrows():
        lemmatized_text=row['article_text_processed_lemmatized'].split()
        pos_taggs=row['article_text_processed_POS'].split()
        for i in range(len(lemmatized_text)):
            lemma = lemmatized_text[i]
            if lemma=='_':
                continue
            tag=pos_taggs[i]
            if lemma not in word_pos_tags:
                word_pos_tags[lemma]=[tag[0]]
            elif tag[0] not in word_pos_tags[lemma]:
                word_pos_tags[lemma].append(tag[0])
    return word_pos_tags

def words_to_pos(region_name):
    df_file_path='../../pre-processing/data/'+region_name+'.pkl'
    df=pd.read_pickle(df_file_path)
    return list_word_pos(df)


words_of_interest_slovene=['azilant','migrant','prebežnik']
words_of_interest_english=['asylum','seeker','migrant','refugee']
regions_slovene=['Slovenia']

model_dir='../../data_modeling/models/'
for filename in os.listdir(model_dir):
    if filename.endswith(".model"):
        region_name = filename[:filename.index('_word2vec.model')]
        words2pos = words_to_pos(region_name)
        model_file_path = os.path.join(model_dir, filename)
        print('***Article analysis for region:', region_name)
        print('\tRestoring model from file:', model_file_path)
        model=gensim.models.Word2Vec.load(model_file_path)
        print('\t...done.')
        words_of_interest=words_of_interest_slovene if region_name in regions_slovene else words_of_interest_english
        list=''
        print('\tListing words close to:',words_of_interest)
        str0=''
        for word in words_of_interest:
            str1='Closest to word "'+word+'" are:'
            str0+='\n'+str1
            print('\t\t'+str1)
            similar_words=model.wv.most_similar(word, topn=30)
            for sw in similar_words:
                str2='\t'+str(sw)
                str0+='\n'+str2
                print('\t\t'+str2)
        with open('../word_neighborhood/'+region_name+'.txt','w') as file:
            file.write(str0)
        print('\t...done.')
        continue
    else:
        continue