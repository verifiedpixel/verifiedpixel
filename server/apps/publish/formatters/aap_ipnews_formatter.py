# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license


import textwrap
from io import StringIO

from bs4 import BeautifulSoup

from apps.publish.formatters import Formatter
import superdesk
from superdesk.errors import FormatterError
from superdesk.io.iptc import subject_codes


class AAPIpNewsFormatter(Formatter):
    def _set_subject(self, category, article):
        """
        Sets the subject code in the odbc_item based on the category, if multiple subject codes are available
        :param category:
        :param article:
        :return:
        """
        subject_reference = '        '
        # Ensure that there is a subject in the article
        if 'subject' in article and 'qcode' in article['subject'][0]:
            # set the subject reference with the first value, in case we can't do better
            subject_reference = article['subject'][0].get('qcode')
            # we have multiple categories and multiple subjects
            if len(article['subject']) > 1 and len(article['anpa_category']) > 1:
                # we need to find a more relevant subject reference if possible
                all_categories = superdesk.get_resource_service('vocabularies').find_one(req=None, _id='categories')
                ref_cat = [cat for cat in all_categories['items'] if
                           cat['qcode'].upper() == category['qcode'].upper()]
                # check if there is an associated subject with the category
                if ref_cat and len(ref_cat) == 1 and 'subject' in ref_cat[0]:
                    # try to find the lowest level subject that matches
                    ref = 0
                    for s in article['subject']:
                        if s['qcode'][:2] == ref_cat[0]['subject'][:2]:
                            if int(s['qcode']) > ref:
                                ref = int(s['qcode'])
                    if ref > 0:
                        subject_reference = '{0:0>8}'.format(ref)
        return subject_reference

    def format(self, article, subscriber):
        """
        Constructs a dictionary that represents the parameters passed to the IPNews InsertNews stored procedure
        :return: returns the sequence number of the subscriber and the constructed parameter dictionary
        """
        try:
            docs = []
            for category in article.get('anpa_category'):
                pub_seq_num = superdesk.get_resource_service('subscribers').generate_sequence_number(subscriber)
                odbc_item = {'originator': article.get('source', None), 'sequence': pub_seq_num,
                             'category': category.get('qcode'),
                             'headline': article.get('headline', '').replace('\'', '\'\''),
                             'author': article.get('byline', '').replace('\'', '\'\''),
                             'keyword': article.get('slugline', None).replace('\'', '\'\'')}

                odbc_item['subject_reference'] = self._set_subject(category, article)
                if 'subject_reference' in odbc_item:
                    odbc_item['subject'] = subject_codes[odbc_item['subject_reference'][:2] + '000000']
                    if odbc_item['subject_reference'][2:5] != '000':
                        odbc_item['subject_matter'] = subject_codes[odbc_item['subject_reference'][:5] + '000']
                    else:
                        odbc_item['subject_matter'] = ''
                    if not odbc_item['subject_reference'].endswith('000'):
                        odbc_item['subject_detail'] = subject_codes[odbc_item['subject_reference']]
                    else:
                        odbc_item['subject_detail'] = ''
                else:
                    odbc_item['subject_reference'] = '        '

                odbc_item['take_key'] = article.get('anpa_take_key', None)  # @take_key
                odbc_item['usn'] = article.get('unique_id', None)  # @usn
                if article['type'] == 'preformatted':
                    odbc_item['article_text'] = article.get('body_html', '').replace('\'', '\'\'')  # @article_text
                elif article['type'] == 'text':
                    soup = BeautifulSoup(article.get('body_html', ''))
                    text = StringIO()
                    for p in soup.findAll('p'):
                        text.write('\x19\r\n')
                        ptext = p.get_text('\n')
                        for l in ptext.split('\n'):
                            if len(l) > 80:
                                text.write(textwrap.fill(l, 80).replace('\n', ' \r\n'))
                            else:
                                text.write(l + ' \r\n')
                    odbc_item['article_text'] = text.getvalue().replace('\'', '\'\'')

                if 'genre' in article:
                    odbc_item['genre'] = article['genre'][0].get('name', None)
                else:
                    odbc_item['genre'] = 'Current'  # @genre
                if article.get('type', 'text') == 'text':
                    odbc_item['texttab'] = 'x'
                elif article.get('type', None) == 'preformatted':
                    odbc_item['texttab'] = 't'
                odbc_item['wordcount'] = article.get('word_count', None)  # @wordcount
                odbc_item['news_item_type'] = 'News'
                odbc_item['priority'] = article.get('priority', 'r')  # @priority
                odbc_item['service_level'] = 'a'  # @service_level

                odbc_item['selector_codes'] = '3**'
                odbc_item['fullStory'] = 1
                odbc_item['ident'] = '0'  # @ident

                docs.append((pub_seq_num, odbc_item))

            return docs
        except Exception as ex:
            raise FormatterError.AAPIpNewsFormatterError(ex, subscriber)

    def can_format(self, format_type, article):
        return format_type == 'AAP IPNEWS' and article['type'] in ['text', 'preformatted']
