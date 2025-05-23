"""
MoinMoin wiki stats about updated pages

Config example::

    [wiki]
    type = wiki
    wiki test = http://moinmo.in/

The optional key 'api' can be used to change the default
xmlrpc api endpoint::

    [wiki]
    type = wiki
    api = ?action=xmlrpc2
    wiki test = http://moinmo.in/
"""

import xmlrpc.client

from did.base import Config, ConfigError, ReportError
from did.stats import Stats, StatsGroup
from did.utils import item

DEFAULT_API = '?action=xmlrpc2'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Wiki Stats
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WikiChanges(Stats):
    """ Wiki changes """

    def __init__(self, *, option, name=None, parent=None, url=None, api=None):
        self.url = url
        self.api = api or DEFAULT_API
        self.changes = 0
        self.proxy = xmlrpc.client.ServerProxy(f"{url}{self.api}")
        Stats.__init__(self, option, name, parent)

    def fetch(self):
        try:
            changes = self.proxy.getRecentChanges(self.options.since.datetime)
        except (xmlrpc.client.Error, OSError) as error:
            raise ReportError(
                f"Unable to fetch wiki changes from '{self.url}' "
                f"because of '{error}'.") from error
        for change in changes:
            if (change["author"] == self.user.login
                    and change["lastModified"] < self.options.until.date):
                self.changes += 1
                url = self.url + change["name"]
                if url not in self.stats:
                    self.stats.append(url)
        self.stats.sort()

    def header(self):
        """ Show summary header. """
        # Different header for wiki:
        # Updates on xxx: x changes of y pages
        item(
            f'{self.name}: {self.changes} '
            f'change{"" if self.changes == 1 else "s"} '
            f'of {len(self.stats)} page{"" if len(self.stats) == 1 else "s"}',
            level=0,
            options=self.options)

    def merge(self, other):
        """ Merge another stats. """
        Stats.merge(self, other)
        self.changes += other.changes


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Stats Group
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WikiStats(StatsGroup):
    """ Wiki stats """

    # Default order
    order = 700

    def __init__(self, option, name=None, parent=None, user=None):
        StatsGroup.__init__(self, option, name, parent, user)
        try:
            api = Config().item(option, 'api')
        except ConfigError:
            api = None
        for wiki, url in Config().section(option, skip=['type', 'api']):
            self.stats.append(WikiChanges(
                option=wiki, parent=self, url=url, api=api,
                name=f"Updates on {wiki}"))
