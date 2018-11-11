import os
import gensim
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations,chain
from sklearn.manifold import TSNE
from googletrans import Translator #pip3 install git+https://github.com/BoseCorp/py-googletrans.git --upgrade




def list_word_pos(df):
    word_pos_tags={}
    for idx,row in df.iterrows():
        if isinstance(row['article_text_processed_lemmatized'], float):
            continue
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

def load_sentiWordNet(file_path='../external_data_sources/SentiWordNet_3.0.0_20130122.txt'):
    return pd.read_csv(file_path,delimiter='\t',comment='#')

def slo_to_eng(slo_word_list):
    #Reaching API request limit
    translator = Translator()
    print(slo_word_list)
    translations = translator.translate(slo_word_list,src='sl',dest='en')

    '''
    #Reaching API request limit
    #https://stackoverflow.com/questions/49497391/googletrans-api-error-expecting-value-line-1-column-1-char-0?fbclid=IwAR1Av8FtpIiBaTfJaesyR7-Jk63aNp0_JHPU-a6VdvcxZcXkDCZQn3neW0s
    translations=[]
    for w in slo_word_list:
        translator = Translator()
        translations.append(translator.translate(w,src='sl',dest='en'))
    '''
    return [translation.text for translation in translations if len(translation.text.split())==1] #REMOVE CONDITION WHEN WORKING WITH PHRASES

def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x']+.02, point['y'], str(point['val']))

def visualise_model(model,output_file_path):
    vocab = list(model.wv.vocab)
    X = model[vocab]
    tsne = TSNE(n_components=2)
    X_tsne = tsne.fit_transform(X)
    df = pd.DataFrame({'x':X_tsne[:,0],'y':X_tsne[:,1],'vocab':vocab}, index=vocab)
    ax = sns.lmplot('x',
                    'y',
                    data=df,  # Data source
                    fit_reg=False,  # Don't fix a regression line
                    size=10,
                    aspect=2)  # size and dimension
    label_point(df['x'], df['y'], df['vocab'], plt.gca())
    #plt.show()
    plt.savefig(output_file_path,dpi=600)

words_of_interest_slovene=['azilant','migrant','prebežnik']
words_of_interest_english=['asylum','seeker','migrant','refugee']
regions_slovene=['Slovenia']

sentiWordNet=load_sentiWordNet()
sentiWordNet['objectiveScore']=sentiWordNet['PosScore']+sentiWordNet['NegScore']
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
        print('\tVisualising model..')
        if not os.path.exists('../models_scatter_plots'):
            os.makedirs('../models_scatter_plots')

        if region_name in regions_slovene:
            continue
        #visualise_model(model,'../models_scatter_plots/'+region_name+'.png')

        print('...done.')
        words_of_interest=words_of_interest_slovene if region_name in regions_slovene else words_of_interest_english
        combinations_of_words_of_interest=list(chain.from_iterable([combinations(words_of_interest,i) for i in range(1,len(words_of_interest))]))
        print('combos:',combinations_of_words_of_interest)

        file=open('../word_neighborhood/'+region_name+'.txt','w')
        for words_of_interest_combo in combinations_of_words_of_interest:

            print('\tWords closest to:',words_of_interest_combo,'are:')
            similar_words = model.wv.most_similar(words_of_interest_combo, topn=100)
            similar_words_in_english=slo_to_eng([x[0] for x in similar_words]) if region_name in regions_slovene else [x[0] for x in similar_words]
            #similar_words_with_sentiWord_score = [similar_words[x] for x in range(len(similar_words_in_english)) if similar_words_in_english[x] in sentiWordNet['SynsetTerms']]
            similar_adjectives_with_sentiWord_score = [similar_words[x] for x in range(len(similar_words_in_english)) if (region_name in regions_slovene and 'P' in words2pos[similar_words[x][0]]) or (region_name not in regions_slovene and 'J' in words2pos[similar_words[x][0]])]
            similar_adjectives_with_sentiWord_score_str='\t\t'+'\n\t\t'.join([str(x) for x in similar_adjectives_with_sentiWord_score])
            sentiWordNet_relevant_rows=sentiWordNet[(sentiWordNet['SynsetTerms'].isin([x[0] for x in similar_adjectives_with_sentiWord_score])) & (sentiWordNet['POS']=='a')]
            objective_score_mean=np.nanmean(sentiWordNet_relevant_rows['objectiveScore'])

            print('CALCULATE MEAN OF THIS COL:',sentiWordNet_relevant_rows['objectiveScore'])
            print('SIMILAR START')

            print(similar_adjectives_with_sentiWord_score_str)
            print('\t\t\tMEAN OBJECTIVE SCORE:',objective_score_mean)
            file.write('\nWords closest to: '+str(words_of_interest_combo)+' are:\n'+similar_adjectives_with_sentiWord_score_str+'\n\t\tMEAN OBJECTIVE SCORE:'+str(objective_score_mean))
            print('\t...done.')
            continue
        file.close()
    else:
        continue