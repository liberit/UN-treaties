#!/usr/bin/env python

# -*- coding: utf-8 -*-
#    This file is part of liberit.

#    liberit is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    liberit is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with liberit.  If not, see <http://www.gnu.org/licenses/>.

# (C) 2012 Stefan Marsiske <s@ctrlc.hu>


import re, sys
#import lxml.html
from urlparse import urljoin

base="http://treaties.un.org/Pages/ParticipationStatus.aspx"

sigre=re.compile(r'Signature',re.I)
datere=re.compile(r'(Ratification|Accession|Succession|Acceptance)')
countryre=re.compile(r'([^0-9]*)')

from liberit.utils import fetch, jdump, unws, getFrag

def toText(node):
    if node is None: return ''
    return ''.join([x.strip() for x in node.xpath(".//text()") if x.strip()]).replace(u"\u00A0",' ').strip()

def convertRow(cells, fields):
    res={}
    for name, i in fields:
        tmp=toText(cells[i])
        if name=='Country':
            tmp=countryre.search(tmp).group(1)
        if tmp:
            if type(tmp)==type(tuple()):
                res['url']=tmp[1]
                res[name]=unws(tmp[0])
            else:
                res[name]=unws(tmp)
    return res

def toObj(header):
    res=[]
    #print ' | '.join([''.join(x.xpath('.//text()')) for x in header.xpath('.//td')])
    fields={ 'Country': 0}
    for i, field in list(enumerate([''.join(x.xpath('.//text()')) for x in header.xpath('.//td')]))[1:]:
        if sigre.search(field):
            fields['Signature']=i
        elif datere.search(field):
            fields['Ratification/Accession/Succession/Acceptance']=i
    rows=header.xpath('./following-sibling::tr')
    for row in rows:
        items=row.xpath('td')
        value=convertRow(items, fields.items())
        if value:
            res.append(value)
    return res

def scrape():
    for chap in getFrag(base, '//table[@id="ctl00_ContentPlaceHolder1_dgChapterList"]//tr'):
        chapter=''.join(chap.xpath('.//span//text()'))
        url=urljoin(base,chap.xpath('.//a')[0].get('href'))
        print >>sys.stderr, "chapter", chapter, url
        for trty in getFrag(url, '//table[@id="ctl00_ContentPlaceHolder1_dgSubChapterList"]//tr'):
            treaty=trty.xpath('.//a/text()')[0].split('  ')[0]
            tmp=treaty.split(u"\u00A0",1)
            treaty=tmp[0].replace(u"\u00A0",' ').strip()
            if len(tmp)>1:
                city=tmp[1].replace(u"\u00A0",' ').strip()
            else:
                city=None
            url=urljoin(base,trty.xpath('.//a')[0].get('href'))
            print >>sys.stderr, 'treaty', treaty
            print >>sys.stderr, url
            i=0
            header=getFrag(url,'//table//tr[@class="tableHdr"]//*[starts-with(.,"Participant")]/ancestor::tr[1]')
            if len(header)==0:
                continue
            pdf=header[0].xpath('//img[@title="View PDF"]/..')[0].get('href')
            if pdf:
                pdf=urljoin(base,pdf)
            for obj in toObj(header[0]):
                obj['Chapter']=chapter
                obj['Treaty']=treaty
                if city:
                    obj['City']=city
                if pdf:
                    obj['PDF']=pdf
                #scraperwiki.sqlite.save(unique_keys=['Treaty', "Country"],  data=obj)
                yield obj
                i+=1
            print >>sys.stderr, i


print '['
for obj in scrape():
    print jdump(obj).encode('utf8'),','
print ']'

