###
# Copyright (c) 2013, Colton Wolkins
# All rights reserved.
#
#
###

from supybot.test import *

class AssemblaTestCase(PluginTestCase):
    config = {
    'supybot.plugins.Assembla.apiKey': '',
	'supybot.plugins.Assembla.apiSecret': ''
    }
    plugins = ('Assembla',)

    def testTicket(self):
        #self.assertNotError('ticket 10')
        print self.getMsg('ticket 10')
        print self.getMsg('what is #10')
        
class AssemblaChannelTestCase(ChannelPluginTestCase):
    config = {
    'supybot.plugins.Assembla.apiKey': '',
	'supybot.plugins.Assembla.apiSecret': ''
    }
    plugins = ('Assembla',)
    def testChannelTicket(self):
        print self.irc.feedMsg(ircmsgs.action(self.channel, 'what is #10?'))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
