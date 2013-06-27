###
# Copyright (c) 2013, Colton Wolkins
# All rights reserved.
#
#
###
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import requests
import re
import supybot.conf as conf
import supybot.log as log


class Assembla(callbacks.PluginRegexp):
    threaded = True
    callAfter = ['Web']
    regexps = ['webSnarfer']
    ticketRegex = re.compile(r'#?([0-9]+)')
    """The whole purpose of the Assembla plugin is to allow
    users to say a ticket number and the plugin will grab
    all of the basic information about said ticket."""
    def __init__(self, irc):
        self.__parent = super(Assembla, self)
        self.__parent.__init__(irc)
        self.space = None
        self.spaceName = None

    def getConfig(self, irc):
        if self.space is not None:
            return
        self.key = self.registryValue('apiKey', value='')
        self.secret = self.registryValue('apiSecret', value='')
        self.spaceName = self.registryValue('space', value='example')
        self.space = self.getAPI(irc, 'spaces.json')
        if self.space:
            if self.registryValue('debug'):
                irc.reply('Debug: %s' % self.space, prefixNick=False)
            try:
                for json in self.space:
                    if json[u'name'] == self.spaceName:
                        self.space = json[u'id']
            except TypeError:
                irc.reply('Error: Could not get the "%s" Assembla space!' % self.spaceName)
                log.error('%s\n' % (response))
                self.spaces = None
        else:
            self.space = None

    def getAPI(self, irc, url):
        if(self.key is '' or self.secret is ''):
            log.error('Error: Plugin Assembla not configured!')
            return False
        #sys.stderr.write('%s - %s : %s\n' % (self.key, self.secret, url))
        try:
            response = requests.get(
              url='https://api.assembla.com/v1/'+url,
              headers={
                  'X-Api-Key': str(self.key),
                  'X-Api-Secret': str(self.secret),
              },
            )
            if self.registryValue('debug'):
                irc.reply('Debug: Url: %s' % response.url, prefixNick=False)
                irc.reply('Debug: status: %s' % response.status_code, prefixNick=False)
                irc.reply('Debug: history (blank if 1 request): %s' % response.history, prefixNick=False)
                try:
                    irc.reply('Debug: text: %s' % response.text, prefixNick=False)
                except UnicodeEncodeError, e:
                    irc.reply('Error: Cannot encode unicode to ascii', prefixNick=False)
                # irc.reply('Debug: %s' % response.text, prefixNick=False)
        except requests.exceptions.ConnectionError:
            if self.registryValue('debug'):
                irc.reply('Debug: There was a Connection Error between me and Assembla', prefixNick=False)
            return False
        except requests.exceptions.Timeout:
            if self.registryValue('debug'):
                irc.reply('Debug: Connection timed out', prefixNick=False)
            return False
        except requests.exceptions.HTTPError:
            if self.registryValue('debug'):
                irc.reply('Debug: Invalid HTTP response', prefixNick=False)
            return False
        if response.status_code == 200: # OK
            return response.json()
        elif response.status_code == 204:
            if self.registryValue('debug'):
                irc.reply('Debug: 204: No Content', prefixNick=False)
            return False
        else:
            if self.registryValue('debug'):
                irc.reply('Debug: %s? response from server' % response.status_code, prefixNick=False)
            return False

    def ticket(self, irc, msg, args, ticketID):
        """<Ticket ID>

        Gets a ticket from Assembla and returns it's name and status.
        The ticket will be returned in the following format: Assembla Ticket #<Ticket Number>, <Summary> [<Status> - <Priority>]
        """
        ticketID = int(self.ticketRegex.match(ticketID).group(1))
        self.getConfig(irc)
        if(self.key is '' or self.secret is ''):
            irc.reply('Bot Error: Plugin not configured!')
            return
        if self.registryValue('debug'):
            irc.reply('Debug: Grabbing ticket', prefixNick=False)
        if self.space is not None:
            ticket = self.getAPI(irc, 'spaces/%s/tickets/%d.json' % (self.space, ticketID))
            if ticket is not False:
                message = 'Assembla Ticket #%d, %s [%s - %d]' % (ticketID, ticket[u'summary'], ticket[u'status'], ticket[u'priority'])
                irc.reply(message)
                if self.registryValue('urlGen'):
                    irc.reply('https://www.assembla.com/spaces/%s/tickets/%d' % (self.spaceName, ticketID))
            else:
                irc.reply("Failed to retrieve ticket #%s" % ticketID)
    ticket = wrap(ticket, ['anything'])

    def webSnarfer(self, irc, msg, match):
        r'#([0-9]+)'
        if(msg.nick.lower().endswith('bot')):
            return
        if self.registryValue('debug'):
            irc.reply(msg.args, prefixNick=False)
        channel = msg.args[0]
        if msg.args[1].startswith(conf.supybot.reply.whenAddressedBy.chars()):
            return
        matches = re.findall(r'#([0-9]+)', msg.args[1], re.S)
        # print matches
        if not irc.isChannel(msg.args[0]):
            #irc.reply("Ticket snarfing disabled.", prefixNick=True)
            return
        # irc.reply(msg)
        # irc.reply(match.group(1))
        if not self.registryValue('ticketSnarfer', channel):
            return
        self.getConfig(irc)
        if self.registryValue('debug'):
            tickets = ''
            for id in matches:
                tickets = tickets + ' '
            irc.reply('Debug: You asked for: %s' % tickets, prefixNick=False)
        for id in matches:
            self._ticketGet(irc, id)
    webSnarfer = urlSnarfer(webSnarfer)
    # webSnarfer.__doc__ = re.compile(r'#([0-9]+)')

    def _ticketGet(self, irc, match):
        ticketID = int(match)
        if self.registryValue('debug'):
            irc.reply('Debug: Grabbing ticket', prefixNick=False)
        if self.space is not None:
            ticket = self.getAPI(irc, 'spaces/%s/tickets/%d.json' % (self.space, ticketID))
            if ticket is not False:
                message = 'Assembla Ticket #%d, %s [%s - %d]' % (ticketID, ticket[u'summary'], ticket[u'status'], ticket[u'priority'])
                irc.reply(message, prefixNick=False)
                if self.registryValue('urlGen'):
                    irc.reply('https://www.assembla.com/spaces/%s/tickets/%d' % (self.spaceName, ticketID), prefixNick=False)
            else:
                irc.reply("Failed to retrieve ticket #%s" % ticketID, prefixNick=False)

Class = Assembla


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
