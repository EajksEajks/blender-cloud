#!/usr/bin/env python3

from __future__ import print_function

"""CLI command for sharing an image via Blender Cloud.

Assumes that you are logged in on Blender ID with the Blender ID Add-on.

The user_config_dir and user_data_dir functions come from
 https://github.com/ActiveState/appdirs/blob/master/appdirs.py and
 are licensed under the MIT license.
"""

import argparse
import json
import mimetypes
import os.path
import pprint
import sys
import webbrowser

from urllib.parse import urljoin

import requests

cli = argparse.Namespace()  # CLI args from argparser
sess = requests.Session()
IMAGE_SHARING_GROUP_NODE_NAME = 'Image sharing'

if sys.platform.startswith('java'):
    import platform

    os_name = platform.java_ver()[3][0]
    if os_name.startswith('Windows'):  # "Windows XP", "Windows 7", etc.
        system = 'win32'
    elif os_name.startswith('Mac'):  # "Mac OS X", etc.
        system = 'darwin'
    else:  # "Linux", "SunOS", "FreeBSD", etc.
        # Setting this to "linux2" is not ideal, but only Windows or Mac
        # are actually checked for and the rest of the module expects
        # *sys.platform* style strings.
        system = 'linux2'
else:
    system = sys.platform


def request(method: str, rel_url: str, **kwargs) -> requests.Response:
    kwargs.setdefault('auth', (cli.token, ''))
    url = urljoin(cli.server_url, rel_url)
    return sess.request(method, url, **kwargs)


def get(rel_url: str, **kwargs) -> requests.Response:
    return request('GET', rel_url, **kwargs)


def post(rel_url: str, **kwargs) -> requests.Response:
    return request('POST', rel_url, **kwargs)


def find_user_id() -> str:
    """Returns the current user ID."""

    print(15 * '=', 'User info', 15 * '=')
    resp = get('/api/users/me')
    resp.raise_for_status()

    user_info = resp.json()
    print('You are logged in as %(full_name)s (%(_id)s)' % user_info)

    return user_info['_id']


def find_home_project_id() -> dict:
    resp = get('/api/bcloud/home-project')
    resp.raise_for_status()

    proj = resp.json()
    proj_id = proj['_id']
    print('Your home project ID is %s' % proj_id)
    return proj_id


def find_image_sharing_group_id(home_project_id, user_id) -> str:
    """Find the top-level image sharing group node."""

    node_doc = {
        'project': home_project_id,
        'node_type': 'group',
        'name': IMAGE_SHARING_GROUP_NODE_NAME,
        'user': user_id,
    }

    resp = get('/api/nodes', params={'where': json.dumps(node_doc)})
    resp.raise_for_status()
    items = resp.json()['_items']

    if not items:
        print('Share group not found, creating one.')
        node_doc.update({
            'properties': {},
        })
        resp = post('/api/nodes', json=node_doc)
        resp.raise_for_status()
        share_group = resp.json()
    else:
        share_group = items[0]

    # print('Share group:', share_group)
    return share_group['_id']


def upload_image():
    user_id = find_user_id()
    home_project_id = find_home_project_id()
    group_id = find_image_sharing_group_id(home_project_id, user_id)
    basename = os.path.basename(cli.imgfile)
    print('Sharing group ID is %s' % group_id)

    # Upload the image to the project.
    print('Uploading %r' % cli.imgfile)
    mimetype, _ = mimetypes.guess_type(cli.imgfile, strict=False)
    with open(cli.imgfile, mode='rb') as infile:
        resp = post('api/storage/stream/%s' % home_project_id,
                    files={'file': (basename, infile, mimetype)})
    resp.raise_for_status()
    file_upload_resp = resp.json()
    file_upload_status = file_upload_resp.get('_status') or file_upload_resp.get('status')
    if file_upload_status != 'ok':
        raise ValueError('Received bad status %s from Pillar: %s' %
                         (file_upload_status, json.dumps(file_upload_resp)))
    file_id = file_upload_resp['file_id']
    print('File ID is', file_id)

    # Create the asset node
    asset_node = {
        'project': home_project_id,
        'node_type': 'asset',
        'name': basename,
        'parent': group_id,
        'properties': {
            'content_type': mimetype,
            'file': file_id,
        },
    }
    resp = post('api/nodes', json=asset_node)
    resp.raise_for_status()
    node_info = resp.json()
    node_id = node_info['_id']
    print('Created asset node', node_id)

    # Share the node to get a public URL.
    resp = post('api/nodes/%s/share' % node_id)
    resp.raise_for_status()
    share_info = resp.json()
    print(json.dumps(share_info, indent=4))

    url = share_info.get('short_link')
    print('Opening %s in a browser' % url)
    webbrowser.open_new_tab(url)


def find_credentials():
    """Finds BlenderID credentials.

    :rtype: str
    :returns: the authentication token to use.
    """
    import glob

    # Find BlenderID profile file.
    configpath = user_config_dir('blender', 'Blender Foundation', roaming=True)
    found = glob.glob(os.path.join(configpath, '*'))
    for confpath in reversed(sorted(found)):
        profiles_path = os.path.join(confpath, 'config', 'blender_id', 'profiles.json')
        if not os.path.exists(profiles_path):
            continue

        print('Reading credentials from %s' % profiles_path)
        with open(profiles_path) as infile:
            profiles = json.load(infile, encoding='utf8')
        if profiles:
            break
    else:
        print('Unable to find Blender ID credentials. Log in with the Blender ID add-on in '
              'Blender first.')
        raise SystemExit()

    active_profile = profiles[u'active_profile']
    profile = profiles[u'profiles'][active_profile]
    print('Logging in as %s' % profile[u'username'])

    return profile[u'token']


def main():
    global cli

    parser = argparse.ArgumentParser()
    parser.add_argument('imgfile', help='The image file to share.')
    parser.add_argument('-u', '--server-url', default='https://cloud.blender.org/',
                        help='URL of the Flamenco server.')
    parser.add_argument('-t', '--token',
                        help='Authentication token to use. If not given, your token from the '
                             'Blender ID add-on is used.')

    cli = parser.parse_args()
    if not cli.token:
        cli.token = find_credentials()

    upload_image()


def user_config_dir(appname=None, appauthor=None, version=None, roaming=False):
    r"""Return full path to the user-specific config dir for this application.
        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "roaming" (boolean, default False) can be set True to use the Windows
            roaming appdata directory. That means that for users on a Windows
            network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.
    Typical user config directories are:
        Mac OS X:               same as user_data_dir
        Unix:                   ~/.config/<AppName>     # or in $XDG_CONFIG_HOME, if defined
        Win *:                  same as user_data_dir
    For Unix, we follow the XDG spec and support $XDG_CONFIG_HOME.
    That means, by default "~/.config/<AppName>".
    """
    if system in {"win32", "darwin"}:
        path = user_data_dir(appname, appauthor, None, roaming)
    else:
        path = os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config"))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, version)
    return path


def user_data_dir(appname=None, appauthor=None, version=None, roaming=False):
    r"""Return full path to the user-specific data dir for this application.
        "appname" is the name of application.
            If None, just the system directory is returned.
        "appauthor" (only used on Windows) is the name of the
            appauthor or distributing body for this application. Typically
            it is the owning company name. This falls back to appname. You may
            pass False to disable it.
        "version" is an optional version path element to append to the
            path. You might want to use this if you want multiple versions
            of your app to be able to run independently. If used, this
            would typically be "<major>.<minor>".
            Only applied when appname is present.
        "roaming" (boolean, default False) can be set True to use the Windows
            roaming appdata directory. That means that for users on a Windows
            network setup for roaming profiles, this user data will be
            sync'd on login. See
            <http://technet.microsoft.com/en-us/library/cc766489(WS.10).aspx>
            for a discussion of issues.
    Typical user data directories are:
        Mac OS X:               ~/Library/Application Support/<AppName>
        Unix:                   ~/.local/share/<AppName>    # or in $XDG_DATA_HOME, if defined
        Win XP (not roaming):   C:\Documents and Settings\<username>\Application Data\<AppAuthor>\<AppName>
        Win XP (roaming):       C:\Documents and Settings\<username>\Local Settings\Application Data\<AppAuthor>\<AppName>
        Win 7  (not roaming):   C:\Users\<username>\AppData\Local\<AppAuthor>\<AppName>
        Win 7  (roaming):       C:\Users\<username>\AppData\Roaming\<AppAuthor>\<AppName>
    For Unix, we follow the XDG spec and support $XDG_DATA_HOME.
    That means, by default "~/.local/share/<AppName>".
    """
    if system == "win32":
        raise RuntimeError("Sorry, Windows is not supported for now.")
    elif system == 'darwin':
        path = os.path.expanduser('~/Library/Application Support/')
        if appname:
            path = os.path.join(path, appname)
    else:
        path = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))
        if appname:
            path = os.path.join(path, appname)
    if appname and version:
        path = os.path.join(path, version)
    return path


if __name__ == '__main__':
    main()
