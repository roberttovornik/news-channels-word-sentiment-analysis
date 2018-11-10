import os
import zipfile

def unzip_all_models(zip_dir, unzip_dir):

    for _, _, files in os.walk(zip_dir):
        for file in files:
            if file.endswith('.zip'):
                zipped_file = zipfile.ZipFile(os.path.join(zip_dir, file))
                zipped_file.extractall(unzip_dir)     
                zipped_file.close()

def main():
    zipped_dir = "models-zipped"
    unzip_dir = "models-unzipped"

    if not os.path.exists(unzip_dir):
    	os.makedirs(unzip_dir)

    unzip_all_models(zipped_dir, unzip_dir)

if __name__ == "__main__":
    main()