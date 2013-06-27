###
# Copyright (c) 2013, Colton Wolkins
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    assembla = conf.registerPlugin('Assembla', True)
    if yn("Would you like to configure Assembla now?", default=False):
    	key = something("Please enter an API key", '')
    	secret = something("Please enter an API Secret", '')
    	assembla.apiKey.setValue(key)
    	assembla.apiSecret.setValue(Secret)
    if yn('Do you want the Assembla snarfer enabled by default?'):
        conf.supybot.plugins.Google.ticketSnarfer.setValue(True)


Assembla = conf.registerPlugin('Assembla')

############### GLOBALS ##################
conf.registerGlobalValue(Assembla, 'apiKey',
    registry.String('', """Assembla API Key/Secret pair for accessing Assembla"""))
conf.registerGlobalValue(Assembla, 'apiSecret',
    registry.String('', """Assembla API Key/Secret pair for accessing Assembla"""))
conf.registerGlobalValue(Assembla, 'debug',
    registry.Boolean(False, """Extra Verbose Mode! =D"""))
conf.registerGlobalValue(Assembla, 'space',
    registry.String('', """Assembla space"""))

############### CHANNELS ##################
conf.registerChannelValue(Assembla, 'ticketSnarfer',
    registry.Boolean(False, """Determines whether the ticket snarfer is
    enabled.  If so, messages that contain a # immediately followed by
    a number will have the ticket information sent to the channel."""))
conf.registerChannelValue(Assembla, 'urlGen',
    registry.Boolean(False, """Generate URLs and output them when a ticket is mentioned"""))
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Assembla, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
