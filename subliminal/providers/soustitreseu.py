# -*- coding: utf-8 -*-
# Copyright 2012 Nicolas Wack <wackou@gmail.com>
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
from . import ServiceBase
from ..cache import cachedmethod
from ..language import language_set, Language
from ..subtitles import get_subtitle_path, ResultSubtitle
from ..utils import get_keywords
from ..videos import Episode
from bs4 import BeautifulSoup
import logging
import socket
import re


logger = logging.getLogger(__name__)


def match(pattern, string):
    try:
        return re.search(pattern, string).group(1)
    except AttributeError:
        logger.debug(u'Could not match %r on %r' % (pattern, string))
        return None


class SousTitresEU(ServiceBase):
    server_url = 'http://www.sous-titres.eu'
    api_based = False
    languages = language_set(['en', 'fr'])
    videos = [Episode]
    require_video = False
    required_features = ['permissive']

    def list_checked(self, video, languages):
        return self.query(video.path or video.release, languages, get_keywords(video.guess), video.series, video.season, video.episode)

    def query(self, filepath, languages, keywords, series, season, episode):
        logger.debug(u'Getting subtitles for %s season %d episode %d with languages %r' % (series, season, episode, languages))
        self.init_cache()
        subtitles = []
        r = self.session.get('%s/series/%s.xml' % (self.server_url, series.lower().replace(" ","_")))
        seasonEpisodeRegex = re.compile(".*([0-9]{1,2})x([0-9]{1,2})\.(\w*)\.")
        soup = BeautifulSoup(r.content, "xml")
        for item in soup('item'):
            title = item.title.get_text()
            matches_season_episode = seasonEpisodeRegex.match(title)
            if matches_season_episode: 
                (season_found, episode_found, lang_found) = matches_season_episode.groups()
                if int(season_found.strip()) == season  and int(episode_found.strip()) == episode :
                    sub_link = item.link.get_text()
                    get_lang = re.match(r'(\w{2})(\w{2})*',lang_found)
                    for lang in get_lang.groups():
                        if Language(lang) in languages :
                            sub_path = get_subtitle_path(filepath, lang, self.config.multi)
                            sub_lang = Language(lang)
                            subtitle = ResultSubtitle(sub_path, sub_lang, self.__class__.__name__.lower(), sub_link) 
                            subtitles.append(subtitle)
                            break
                    break 
                else :
                    continue
            else:
                continue
        return subtitles

    def download(self, subtitle):
        self.download_zip_file(subtitle.link, subtitle.path)
        return subtitle

Service = SousTitresEU 
