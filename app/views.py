# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, session, url_for, request, \
    g, jsonify
from app import app #, db, lm, oid, babel
import redis
from urllib import urlencode
import httplib2
import json
import ast
from werkzeug.contrib.cache import MemcachedCache
import operator

CLIENT_ID = 'd803438f727b4e1b9fa8a37ebd74a4f6'
h = httplib2.Http(".cache")
access_token = 0


redis_connections = redis.Redis()


@app.route("/")
@app.route("/insta")
@app.route("/insta/")
def insta():
    res = ''
    # search_instagram("동국대",2);
    # print "total length : " + str(len(res))
    return render_template('insta_search.html', tag_result = res)

@app.route("/deep/")
@app.route("/deep")
def deep():
    deep_search_rank = request.args.get('deep_search_rank')
    deep_search_number = request.args.get('deep_search_number')

    res = deep_search_instagram(int(deep_search_rank),int(deep_search_number));

    tag_res = []
    tagDict = {}
    print len(res)
    for eachRes in res:
        tag_res = eachRes['tags']
        for eachTag in tag_res:
            if not eachTag in tagDict:
                tagDict[eachTag] = 1
            else:
                tagDict[eachTag] += 1
    sortedDict = sorted(tagDict.items(), key = operator.itemgetter(1), reverse=True)
    return render_template('insta_search.html', tag_result = session['tag_res'], tag_list = session['tag_dict'], deep_tag_result = res, deep_tag_list = sortedDict)


@app.route("/insta/<search_str>")
def insta_res(search_str):
    res = []
    next_url = ''
    redis_search_cache = {}
    number = int(request.args.get('number'))

    if not isinstance(number, int ):
        return '숫자 입력해'
    redis_str = redis_connections.get(search_str)
    # print 'redis_str',redis_str
    
    redis_search_cache = ast.literal_eval(redis_str)
    
    if redis_search_cache is not None:
        search_len = number - len(redis_search_cache)
        next_url = redis_search_cache['next_url']
        print search_len
        if search_len < 0:
            res = redis_search_cache['res_list'][:(number*20)]
        elif search_len == 0:
            res = redis_search_cache['res_list']
        else:
            res = search_instagram(search_str, search_len, next_url)
            redis_search_cache['res_list'].extend(res['data'])
            redis_search_cache['next_url'] = res['next_url']
    else:
        redis_search_cache = {}
        res = search_instagram(search_str,number,0);
        redis_search_cache['res_list'] = res['data']
        redis_search_cache['next_url'] = res['next_url']

    redis_connections.set(search_str, redis_search_cache)

    tagDict = {}
    for eachRes in res:
        for eachTag in eachRes['tags']:
            if not eachTag in tagDict:
                tagDict[eachTag] = 1
            else:
                tagDict[eachTag] += 1
    
    sortedDict = sorted(tagDict.items(), key = operator.itemgetter(1), reverse=True)

    return render_template('insta_search.html', tag_result = res, tag_list = sortedDict)




def deep_search_instagram(deep_search_rank, deep_search_number):
    res_list = []
    next_url = 0
    print "deep search rank : "  + str(deep_search_rank)
    print "deep search number : " + str(deep_search_number)
    j=0
    i=0
    while j < deep_search_rank:
        while i < deep_search_number:
            i+=1
            print "page : " + str(i)
            if next_url!=0:
                resp, content = h.request(next_url)
            else:
                resp, content = h.request("https://api.instagram.com/v1/tags/"+unicode(session['tag_dict'][j][0].encode("utf-8"),"utf-8")+"/media/recent?client_id=d803438f727b4e1b9fa8a37ebd74a4f6&COUNT=20")
            json_res = json.loads(content)

            data_res = json_res['data']
            for each in data_res:
                res_list.append(each)

            if not 'next_url' in json_res['pagination'].keys():
                break
            else:
                next_url = json_res['pagination']['next_url']
        j+=1
    return res_list


def search_instagram(tag_name, search_len, next_url):
    res_dict = {}
    res_list = []
    print "search name : "  + tag_name
    print "search page : " + str(search_len)

    i=0

    while i < search_len:
        i+=1
        print "page : " + str(i)
        if next_url!=0:
            resp, content = h.request(next_url)
        else:
            resp, content = h.request("https://api.instagram.com/v1/tags/"+unicode(tag_name.encode("utf-8"),"utf-8")+"/media/recent?client_id=d803438f727b4e1b9fa8a37ebd74a4f6&COUNT=20")
        
        json_res = json.loads(content)

        data_res = json_res['data']
        for each in data_res:
            res_list.append(each)

        if not 'next_url' in json_res['pagination'].keys():
            break
        else:
            next_url = json_res['pagination']['next_url']
    res_dict['data'] = res_list
    res_dict['next_url'] = next_url
    return res_dict
