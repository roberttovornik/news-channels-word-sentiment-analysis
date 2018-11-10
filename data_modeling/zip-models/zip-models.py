import os
import zipfile

def zip_each_file(directory, zip_dir):

    for _, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.model'):
                zip_dest = os.path.join(zip_dir, file.replace(".model", ".zip"))
                zipped_file = zipfile.ZipFile(zip_dest, 'w')
                zipped_file.write(os.path.join(directory, file), arcname=file, compress_type=zipfile.ZIP_DEFLATED)
                zipped_file.close()

def main():
    
    models_dir = "../models"
    zip_dir = "models-zipped"

    if not os.path.exists(zip_dir):
        os.makedirs(zip_dir)

    zip_each_file(models_dir, zip_dir)

if __name__ == "__main__":
    main()