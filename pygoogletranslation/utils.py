"""A conversion module for googletrans"""
import json
import nltk
import unidecode
from pygoogletranslation.constants import (
    LANGCODES, LANGUAGES, RPCIDS
)
from pygoogletranslation.models import TranslatedPart

def format_querystringlang():
    querystring = {
        "client":"te",
    }
    return querystring

def format_querystring(token, text, src='auto', dest='en'):
    querystring = {
        "anno":"3",
        "format":"html",
        "key":"",
        "logld":"vTE_20201130_00",
        "client":"te",
        "v":"1.0",
        "sl": src,
        "tl": dest,
        "tk": token,
        "q": text.encode('utf-8'),
        "tc":"1",
        "sr":"1",
        "mode":"1"
    }
    return querystring


def format_param(rpcids):
    params = {
        'rpcids': rpcids,
        'bl': 'boq_translate-webserver_20201207.13_p0', 
        'soc-app': 1, 
        'soc-platform': 1, 
        'soc-device': 1, 
        'rt': 'c'
    }
    return params

def format_data(rpcids, text, src, dest):
        return {'f.req': json.dumps([[
            [
                rpcids,
                json.dumps([[text, src, dest, True],[None]], separators=(',', ':')),
                None,
                'generic',
            ],
        ]], separators=(',', ':'))}

def format_response_legacy(a):
    result = {}
    b = a.split('\n')
    li_filter = []
    flag = False
    for _b in b:
        if _b.isnumeric():
            flag = not flag
            _b = 'pygoogletranslation'
        if flag:
            li_filter.append(_b)
    fi_data = str(''.join(li_filter)).replace('"[', '[').replace(']"', ']').replace('\\n', '').replace('\\','')    
    li_data = json.loads(fi_data.split('pygoogletranslation')[1].replace('"[', '[').replace(']"', ']'))
    return li_data

def format_response(datalist):
    translatedlist = []
    for data in datalist:
        transdata = []
        token_found = False
        square_bracket_counts = [0, 0]
        resp = ''
        for line in data.split('\n'):
            token_found = token_found or f'"{RPCIDS}"' in line[:30]            
            if not token_found:
                continue

            is_in_string = False
            for index, char in enumerate(line):
                if char == '\"' and line[max(0, index - 1)] != '\\':
                    is_in_string = not is_in_string
                if not is_in_string:
                    if char == '[':
                        square_bracket_counts[0] += 1
                    elif char == ']':
                        square_bracket_counts[1] += 1

            resp += line
            if square_bracket_counts[0] == square_bracket_counts[1]:
                break

        data = json.loads(resp)
        parsed = json.loads(data[0][2])
        # not sure
        should_spacing = parsed[1][0][0][3]
        translated_parts = list(map(lambda part: TranslatedPart(part[0], part[1] if len(part) >= 2 else []), parsed[1][0][0][5]))
        translated = (' ' if should_spacing else '').join(map(lambda part: part.text, translated_parts))
        transdata.append(translated)

        
        try:
            transdata.append(parsed[2])
        except:
            transdata.append('auto')
       
        try:
            transdata.append(parsed[0][2])
        except:
            transdata.append('auto')

        # currently not available
        confidence = None

        origin_pronunciation = None
        try:
            transdata.append(parsed[0][0])
        except:
            transdata.append('')

        pronunciation = None
        try:
            transdata.append(parsed[1][0][0][1])
        except:
            transdata.append()

        translatedlist.append(transdata)
    return translatedlist

def _format_response(a):
    result = {}
    b = a.split('\n')
    li_filter = []
    flag = False
    for _b in b:
        if _b.isnumeric():
            flag = not flag
            _b = 'pygoogletranslation'
        if flag:
            # Parsing to cleanup "unescaped escaped" characters
            if '\\' in _b:
                _bp = ''
                p = 0
                while p < len(_b):
                    if _b[p:p+2] == '\\\\':
                        _bp += '\\'
                        p += 2
                    elif _b[p:p+1] == '\\':
                        if _b[p:p+2] == '\\u':
                            _bp += bytes(_b[p:p+6], 'ascii').decode('unicode-escape')
                            p += 6
                        elif _b[p:p+2] == '\\n':
                            _bp += '\n'
                            p += 2
                        else:
                            p += 1
                    else:
                        _bp += _b[p:p+1]
                        p += 1
                _b = _bp

            li_filter.append(_b)
    fi_data = str(''.join(li_filter)).replace('","[', '",[', 1).replace('\n",null', '\n,null')
    li_data = json.loads(fi_data.split('pygoogletranslation')[1], strict=False)
    return li_data
    
def tokenize_sentence(text):
    text_len = 0
    token_text = ''
    text_list = []
    if len(text) <= 5000:
        text_list.append(text)
        return text_list
    tokens = nltk.sent_tokenize(text)
    for t in tokens:
        text_len += len(t)
        if text_len < 5000:
            token_text += t
        else:
            text_list.append(token_text)
            text_len = 0
            token_text = t
    if text_len < 5000:
        text_list.append(token_text)
    return text_list


def format_translation(translated):
    text = ''
    pron = ''
    for _translated in translated:
        try:
            text += _translated[0][2][1][0][0][5][0][0]
            #text += "".join([e[0] for e in data[0][2][1][0][0][5]])
        except:
            text += fix_trans_error(_translated)
        try:
            pron += unidecode.unidecode(_translated[0][2][1][0][0][1])
        except:
            pron += ''

    for _translated in translated:
        try:
            _translated[0][2][1][0][0][5][0][0] = text
            break
        except:
            pass
    try:
        _translated[0][2][1][0][0][1] = pron
    except:
        pass
    return _translated


def fix_trans_error_legacy(translated):
    if len(translated) > 0:
        if len(translated[0]) > 2:
            if len(translated[0][2]) > 1:
                if len(translated[0][2][1]) > 0:
                    if len(translated[0][2][1][0]) > 0:
                        if len(translated[0][2][1][0][0]) > 5:
                            if len(translated[0][2][1][0][0][5]) > 0:
                                if len(translated[0][2][1][0][0][5][0]) > 0:
                                    text = translated[0][2][1][0][0][5][0][0]
                                else:
                                    text = translated[0][2][1][0][0][5][0]
                            else:
                                text = translated[0][2][1][0][0][5]
                        else:
                            text = translated[0][2][1][0][0]
                    else:
                        text = translated[0][2][1][0]
                else:
                    text = translated[0][2][1]
            else:
                text = translated[0][2]
        else:
            text = translated[0]
    else:
        text = translated
    return str(text)


def fix_trans_error(translated):
    if len(translated) > 0:
        if len(translated[0]) > 2:
            if len(translated[0][2]) > 1:
                if len(translated[0][2][1]) > 0:
                    if len(translated[0][2][1][0]) > 0:
                        if len(translated[0][2][1][0][0]) > 5:
                            if translated[0][2][1][0][0][5] is None:
                                text = translated[0][2][1][0][0][0]
                            elif len(translated[0][2][1][0][0][5]) > 0:
                                if len(translated[0][2][1][0][0][5][0]) > 0:
                                    text = translated[0][2][1][0][0][5][0][0]
                                else:
                                    text = translated[0][2][1][0][0][5][0]
                            else:
                                text = translated[0][2][1][0][0][5]
                        else:
                            text = translated[0][2][1][0][0]
                    else:
                        text = translated[0][2][1][0]
                else:
                    text = translated[0][2][1]
            else:
                text = translated[0][2]
        else:
            text = translated[0]
    else:
        text = translated
    return str(text)

