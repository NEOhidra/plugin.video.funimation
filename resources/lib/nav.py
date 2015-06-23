# -*- coding: utf-8 -*-
import os
import sys
import logging
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import utils
from .funimation import Funimation, WatchQueue
from .funimation.models import Show

log = logging.getLogger('funimation')
handle = int(sys.argv[1])
addon = xbmcaddon.Addon()

cookie_file = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')),
                           'fun-cookie.txt')
api = Funimation(addon.getSetting('username'), addon.getSetting('password'),
                 cookie_file)

queue_db = os.path.join(xbmc.translatePath(addon.getAddonInfo('profile')),
                        'queue.db')
queue = WatchQueue(queue_db)

_ = utils.get_string
# static menu items
menus = (
    {'label': _('browse_shows'),      'get': 'shows'},
    {'label': _('browse_latest'),     'get': 'shows', '_filter': 'latest'},
    {'label': _('browse_simulcasts'), 'get': 'shows', '_filter': 'simulcast'},
    {'label': _('browse_featured'),   'get': 'shows', '_filter': 'featured'},
    {'label': _('browse_genre'),      'get': 'genres'},
    {'label': _('browse_alpha'),      'get': 'alpha'},
    {'label': _('search'),            'get': 'search'},
    {'label': _('queue'),             'get': 'queue'},
)


def list_menu():
    params = utils.get_params()
    if params.get('get'):
        generate_menu(params)
    else:
        for menu in menus:
            add_list_item(menu)
    if handle > -1:
        xbmcplugin.endOfDirectory(handle)


def generate_menu(query):
    action = query.get('get')
    if action == 'shows':
        xbmcplugin.setContent(handle, 'tvshows')
        if query.get('_filter') == 'genre':
            results = api.get_shows_by_genre(query['label'])
        elif query.get('_filter') == 'latest':
            results = api.get_latest()
        elif query.get('_filter') == 'simulcast':
            results = api.get_simulcast()
        elif query.get('_filter') == 'featured':
            results = api.get_featured()
        else:
            results = api.get_shows(first_letter=query.get('alpha'))
        add_shows(results)

    elif action == 'videos':
        xbmcplugin.setContent(handle, 'episodes')
        results = api.get_videos(query['show_id'])
        add_videos(results)

    elif action == 'search':
        results = api.search(utils.get_user_input('Search'))
        add_shows(results)
        add_videos(results)

    elif action == 'genres':
        for genre in api.get_genres():
            add_list_item({'label': genre, 'get': 'shows', '_filter': 'genre'})

    elif action == 'alpha':
        for i in list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            add_list_item({'label': i, 'get': 'shows', 'alpha': i})
        add_list_item({'label': '#', 'get': 'shows', 'alpha': 'non-alpha'})

    elif action == 'queue':
        if query.get('action') == 'add':
            queue.add_show(api.get_show(query.get('show_id')))
        elif query.get('action') == 'remove':
            queue.remove_show(query.get('show_id'))
        else:
            add_shows(queue.shows)


def add_videos(results):
    # 0=both, 1=sub, 2=dub
    sub_dub = int(addon.getSetting('sub_dub'))
    total = len(results)
    for video in results:
        if sub_dub == 1 and video.sub:
            add_list_item(video.query, video, total)
        elif sub_dub == 2 and video.dub:
            add_list_item(video.query, video, total)
        elif sub_dub == 0:
            add_list_item(video.query, video, total)


def add_shows(results):
    if results:
        total = len(results)
        for show in results:
            add_list_item(show.query, show, total)
    else:
        add_list_item({'label': _('no_results')})


def add_list_item(query, item=None, total=0):
    if item is None:
        item = query

    li = new_list_item(item)
    if item.get('video_url'):
        url = item.get('video_url')
        is_folder = False
        li.setProperty('Is_playable', 'true')
        li.addStreamInfo('video', item.get('stream_info'))
    else:
        is_folder = True
        url = utils.build_url(query)

    if isinstance(item, Show):
        if 'queue' in utils.get_params().values():
            add_context_menu(li, 'Remove from Queue', item.query_queue_remove)
        else:
            add_context_menu(li, 'Add to Queue', item.query_queue_add)
    xbmcplugin.addDirectoryItem(handle, url, li, is_folder, total)


def new_list_item(item):
    li = xbmcgui.ListItem(item.get('label'), item.get('label2'),
                          item.get('icon'), item.get('thumbnail'))
    if item.get('info'):
        li.setInfo('video', item.get('info'))

    return li

def add_context_menu(li, label, query):
    item = (label,
        'RunScript({0},-1,?{1})'.format(addon.getAddonInfo('id'), query))
    li.addContextMenuItems([item])
