# -*- coding: utf-8 -*-
import re
import sys

from lxml import etree

from wikiedits.wiki import WikiExtractor

HTML_TAG_REGEX = r'<[^>]{1,20}?>'


class WikiDumpParser:

    def __init__(self, filename):
        self.context = etree.iterparse(filename)
        self.important_tags = ['id', 'timestamp', 'comment', 'text', 'title']

    def clean_rev_iter(self):
        for revision in self.rev_iter():
            if revision['text'] is None:
                continue
            revision['text'] = self.clean_markups(revision['text'])
            yield revision

    def clean_markups(self, text):
        clean_text = WikiExtractor.clean(text)
        tmp = re.sub("http[^\s]+","",clean_text)

        clean_frags = WikiExtractor.compact(clean_text)
        clean_html = [frag
                      for frag in clean_frags]
        return "\n".join(clean_html) if len(clean_html) > 0 else ""

    def rev_iter(self):
        revision, page, contributor = {}, {}, {}

        for elem in self.__fast_iter():
            tag = self.__extract_tag(elem)
            #  print(tag)
            if tag == 'id':
                if 'id' not in page:  # page id
                    page['id'] = elem.text
                elif 'id' not in revision:  # revision id
                    revision['id'] = elem.text
                else:  # user id
                    contributor['id'] = elem.text

            elif tag in ['username', 'ip']:
                contributor[tag] = elem.text

            elif tag == 'contributor':
                revision['contributor'] = contributor

            elif tag == 'revision':
                revision['page'] = page
                yield revision
                revision = {}
                contributor = {}

            elif tag == 'title':
                page['title'] = elem.text

            elif tag == 'page':
                page = {}
                revision = {}
                contributor = {}

            elif tag in self.important_tags:
                revision[tag] = elem.text

    def __fast_iter(self):
        """
        High-performance XML parsing with lxml, see:
        http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
        """
        try:
            for event, elem in self.context:
                if event == 'end':
                    yield elem

                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
        except etree.LxmlError as ex:
            print("Iteration stopped due to lxml exception: {}"
                  .format(ex), file=sys.stderr)
        finally:
            del self.context

    def __extract_tag(self, elem):
        return elem.tag.rsplit('}', 1)[-1]
