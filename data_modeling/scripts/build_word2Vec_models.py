import os
import pandas as pd
import gensim



data_dir_path='../../pre-processing/data/'
for filename in os.listdir(data_dir_path):
    if filename.endswith(".pkl"):
        region_name=filename[:filename.index('.pkl')]
        data_file_path=os.path.join(data_dir_path, filename)
        print('***Building Word2Vec model for region:',region_name)
        print('\tLoading data from file:',data_file_path)
        df=pd.read_pickle(data_file_path)
        print('\t...done.')
        print('\tTraining model...')
        data_train=[x.split() for x in df['article_text_processed_lemmatized'] if not isinstance(x, float)]
        model = gensim.models.Word2Vec(
            data_train,
            size=300,
            window=10,
            min_count=2,
            workers=8)
        model.train(data_train, total_examples=len(data_train), epochs=10)
        print('\t...done.')
        model_file_path='../models/'+region_name+'_word2vec.model'
        print('\tSaving model to:',model_file_path)
        model.save(model_file_path)
        print('\t...done')
        print('...done.')
    else:
        continue
