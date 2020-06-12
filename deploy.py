#!/usr/bin/python3
#
# Copyright (C) 2019 Oleg Shnaydman edited 2020 Pradana Setialana
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os
import argparse
import requests
import json
import re

DROPBOX_ERROR_CODE = 1
OUTPUT_FILE_PARSING_ERROR = 5

DROPBOX_UPLOAD_ARGS = {
    'path': None,
    'mode': 'overwrite',
    'autorename': True,
    'strict_conflict': True
}
DROPBOX_UPLOAD_URL = 'https://content.dropboxapi.com/2/files/upload'

DROPBOX_SHARE_DATA = {
    'path': None,
    'settings': {
        'requested_visibility': 'public'
    }
}
DROPBOX_SHARE_URL = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'

DROPBOX_DELETE_DATA = {
    'path' : None
}
DROPBOX_DELETE_URL = 'https://api.dropboxapi.com/2/files/delete_v2'


def upload_to_dropbox(target_file_name, source_file, dropbox_token, dropbox_folder):
    '''Upload file to dropbox
    
    Args:
        target_file_name (str): Uploaded file will be rename to this file name.
        source_file (str): File that is going to be uploaded.
        dropbox_token (str): Dropbox API key.
        dropbox_folder (str): Dropbox target folder.
    Returns:
        str: Shared url for download.
    '''
    dropbox_path = '/{folder}/{file_name}'.format(folder=dropbox_folder, file_name=target_file_name)
    DROPBOX_UPLOAD_ARGS['path'] = dropbox_path
    DROPBOX_SHARE_DATA['path'] = dropbox_path
    DROPBOX_DELETE_DATA['path'] = dropbox_path

    # Try to delete the file before upload
    # It's possible to overwrite but this way is cleaner
    headers = {'Authorization': 'Bearer ' + dropbox_token,
            'Content-Type': 'application/json'}
    
    requests.post(DROPBOX_DELETE_URL, data=json.dumps(DROPBOX_DELETE_DATA), headers=headers)

    headers = {'Authorization': 'Bearer ' + dropbox_token,
               'Dropbox-API-Arg': json.dumps(DROPBOX_UPLOAD_ARGS),
               'Content-Type': 'application/octet-stream'}

    # Upload the file
    r = requests.post(DROPBOX_UPLOAD_URL, data=open(source_file, 'rb'), headers=headers)

    if r.status_code != requests.codes.ok:
        print("Failed: upload file to Dropbox: {errcode}".format(errcode=r.status_code))
        return None

    headers = {'Authorization': 'Bearer ' + dropbox_token,
               'Content-Type': 'application/json'}

    # Share and return downloadable url
    r = requests.post(DROPBOX_SHARE_URL, data=json.dumps(DROPBOX_SHARE_DATA), headers=headers)

    if r.status_code != requests.codes.ok:
        print("Failed: get share link from Dropbox {errcode}".format(errcode=r.status_code))
        return None

    # Replace the '0' at the end of the url with '1' for direct download
    return re.sub('dl=.*', 'raw=1', r.json()['url'])


def get_target_file_name(app_name):
    app_name = app_name.lower()
    return '{name}.apk'.format(name=app_name).replace(' ','')

if __name__ == '__main__':
    # Command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--release.dir', dest='release_dir', help='path to release folder', required=True)
    parser.add_argument('--app.name', dest='app_name', help='app name that will be used as file name', required=True)
    parser.add_argument('--dropbox.token', dest='dropbox_token', help='dropbox access token', required=True)
    parser.add_argument('--dropbox.folder', dest='dropbox_folder', help='dropbox target folder', required=True)

    options = parser.parse_args()
    
    target_app_file = get_target_file_name(options.app_name)

    # Upload app file and get shared url
    file_url = upload_to_dropbox(target_app_file, options.release_dir, options.dropbox_token, options.dropbox_folder)
    if file_url == None:
        exit(DROPBOX_ERROR_CODE)