import os,shutil, tempfile, json
import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore,storage
_root_=os.path.dirname(os.path.abspath(__file__))

def root_join(*args):
    return os.path.join(_root_,*args)

def firebase_app_is_initialized():
    try:
        firebase_admin.get_app()
    except:
        return False
    else:
        return True

def firebase_init_app(cred):
    if firebase_app_is_initialized():
        pass
    else:
        cred_dict=dict(cred)
        with open(root_join('credentials.json'),'w') as f:
            json.dump(cred_dict,f)
        firebase_admin.initialize_app(credentials.Certificate(root_join('credentials.json')))
        os.remove(root_join('credentials.json'))

class FirestoreDocument:
    #A helper object to ease Firestore data manipulation in a json-like manner
    def __init__(self,collection,document):
        self.doc = firestore.client().collection(collection).document(document)
        if not self.doc.get().exists:
            self.doc.set({})
        
    def load(self):
        return self.doc.get().to_dict()

    def dump(self,data):
        self.doc.set(data)

class FirebaseStorage:

    def __init__(self):
        self.bucket=storage.bucket("streampy123.appspot.com")

    def download(self,cloud_file_path,local_file_path):
        blob = self.bucket.blob(cloud_file_path)
        blob.download_to_filename(local_file_path)

    def upload(self,local_file_path,cloud_file_path):
        blob = self.bucket.blob(cloud_file_path)
        blob.upload_from_filename(local_file_path)

    def create_empty_folder(self,folder_path):
        blob = self.bucket.blob(f"{folder_path}/.dummy")
        blob.upload_from_string('')

    def clear_folder(self,cloud_target_folder):
        # List all blobs in the target folder
        blobs = self.bucket.list_blobs(prefix=cloud_target_folder)
        # Delete each blob
        for blob in blobs:
            blob.delete()

    def dump_folder_to_cloud(self,local_folder, cloud_target_folder):
        #clear cloud target folder
        self.clear_folder(cloud_target_folder)

        # Upload local folder contents to the cleared cloud folder
        for foldername, subfolders, filenames in os.walk(local_folder):
            for filename in filenames:
                local_file_path = os.path.join(foldername, filename)
                relative_path = local_file_path[len(local_folder):].lstrip(os.path.sep).replace(os.path.sep, "/")            
                cloud_file_path = os.path.join(cloud_target_folder, relative_path).replace("\\", "/")

                blob = self.bucket.blob(cloud_file_path)
                blob.upload_from_filename(local_file_path)


    def load_folder_from_cloud(self,cloud_folder, target_local_folder):

        # Remove the entire directory tree if it exists, and then recreate it
        if os.path.exists(target_local_folder):
            shutil.rmtree(target_local_folder)
        os.makedirs(target_local_folder)

        # List all blobs in the cloud folder
        blobs = self.bucket.list_blobs(prefix=cloud_folder)
        
        for blob in blobs:
            # Determine the local path for the blob
            relative_blob_path = blob.name[len(cloud_folder):].lstrip('/')
            local_file_path = os.path.join(target_local_folder, relative_blob_path)
            
            # Ensure the directory exists (for nested folders)
            local_file_dir = os.path.dirname(local_file_path)
            if not os.path.exists(local_file_dir):
                os.makedirs(local_file_dir)
            
            # Download the blob to the local file
            blob.download_to_filename(local_file_path)
    
#Mimicks python 'open' command, but reads/writes files on the cloud storage.
class CloudOpen:
    def __init__(self,cloud_file_path, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None,root=''):
        self.cloud_file_path = cloud_file_path
        self.mode = mode
        self.bucket = storage.bucket("streampy123.appspot.com")
        self.blob = self.bucket.blob(cloud_file_path)
        self.local_file = None
        self.local_path = None

        # Create a temporary local file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.local_path = temp_file.name

        # If reading or appending, download the current file from Cloud Storage
        if any(x in mode for x in ['r', 'a', 'rb', 'ab']):
            if self.blob.exists():
                self.blob.download_to_filename(self.local_path)

        # Open local file in specified mode
        self.local_file = open(self.local_path, mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline, closefd=closefd, opener=opener)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.local_file:
            self.local_file.close()
            
            if any(x in self.mode for x in ['w', 'a', 'x', 'wb', 'ab', 'xb']):
                self.blob.upload_from_filename(self.local_path)
                
            os.remove(self.local_path)
            self.local_file = None

    # Delegate methods to the local_file
    def __getattr__(self, name):
        return getattr(self.local_file, name)

    # To handle cases where the method isn't found
    def __setattr__(self, name, value):
        if name in ["cloud_file_path", "mode", "bucket", "blob", "local_file", "local_path"]:
            super().__setattr__(name, value)
        else:
            setattr(self.local_file, name, value)

