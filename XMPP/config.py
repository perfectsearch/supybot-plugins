###
# Copyright (c) 2013, Colton Wolkins
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
import supybot.log as log

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('XMPP', True)


class emailChecker(registry.String):
	"""invalid email"""
	def setValue(self, str):
		import re
		match = re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6}$', str, re.I)
		if not match and str != '' and str.lower() != 'none':
			self.error()
		elif str == '' or str.lower() == 'none':
			registry.String.setValue(self, '')
			return
			log.info(match.group(0))
		registry.String.setValue(self, match.group(0))
class domainChecker(registry.String):
	"""invalid email"""
	def setValue(self, str):
		import re
		match = re.match(r'^[A-Z0-9.-]+\.[A-Z]{2,6}$', str, re.I)
		if not match and str != '' and str.lower() != 'none':
			self.error()
		elif str == '' or str.lower() == 'none':
			registry.String.setValue(self, '')
			return
		registry.String.setValue(self, match.group(0))

XMPP = conf.registerPlugin('XMPP')
conf.registerChannelValue(XMPP, 'nickSnarfer',
    registry.Boolean(False, """Determines whether the nick snarfer is
    enabled.  If so, messages that contain a nick of a user, or an alias
    of said nick, will be notified via XMPP that they've been messaged
    in a channel they aren't in."""))
conf.registerGlobalValue(XMPP, 'domain',
    domainChecker('', """restrict XMPP emails to a specific domain"""))
conf.registerGlobalValue(XMPP, 'telleveryone',
    registry.Boolean(False, """Allow people to use the "Tell Everyone" command"""))

conf.registerGroup(XMPP, 'auth')
conf.registerGlobalValue(XMPP.auth, 'username',
    emailChecker('', """xmpp username/email"""))
conf.registerGlobalValue(XMPP.auth, 'password',
    registry.String('', """xmpp password"""))
# setattr()
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(XMPP, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
