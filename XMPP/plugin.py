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
import ConfigParser, re, os, xmpp
import supybot.conf as conf
import supybot.log as log


class XMPP(callbacks.PluginRegexp):
    """Add the help for "@plugin help XMPP" here
    This should describe *how* to use this plugin."""
    threaded = True
    regexps = ['nickSnarfer']
    # emailRegex = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6}$', re.I)
    emailRegex = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,6}$', re.I)

    def _checkNotChannel(self, irc, msg, password=' '):
        if password and irc.isChannel(msg.args[0]):
            raise callbacks.Error, conf.supybot.replies.requiresPrivacy()

    def touchOpen(self, filename, *args, **kwargs):
        # Open the file in R/W and create if it doesn't exist. *Don't* pass O_TRUNC
        fd = os.open(filename, os.O_RDWR | os.O_CREAT)

        # Encapsulate the low-level file descriptor in a python file object
        return os.fdopen(fd, *args, **kwargs)

    def setemail(self, irc, msg, args, user, otheruser, email):
        """(<user>) <email>
        Set the email for your account. Note: You must be registered with me in
        order to run this command.
        """
        tmpUser = user
        if otheruser is not None and (user._checkCapability('owner') or otheruser is user):
            tmpUser = otheruser
        elif otheruser is not None and not user._checkCapability('owner'):
            irc.reply('Error: You are not authorized to add an alias to another user')
            return
        if self.registryValue('domain'):
            email = re.match(r'^[A-Z0-9._%+-]+@'+self.registryValue('domain').replace('.', '\\.')+'$', email, re.I)
        else:
            email = self.emailRegex.match(email)
        if email is not None:
            email = email.group(0)
            # if irc.isChannel(msg.args[0]):
            #     raise callbacks.Error, conf.supybot.replies.requiresPrivacy()
            try:
                with self.touchOpen(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'), 'r+') as fp:
                    config = ConfigParser.ConfigParser()
                    config.readfp(fp)
                    aliases = []
                    if not config.has_section('Users'):
                        config.add_section('Users')
                    if config.has_option('Users', tmpUser.name):
                        aliases = config.get('Users', tmpUser.name).split(" ")
                        if not not aliases:
                            aliases.pop(0)
                    config.set('Users', tmpUser.name, email + " " + " ".join(aliases))
                    fp.truncate()
                    fp.seek(0)
                    config.write(fp)
                    fp.truncate()
                    fp.close()
                    irc.replySuccess()
            except Exception, e:
                log.error(str(e))
                irc.replyError("Error: Failed to save your email to the config file.")
        elif email is None:
            if self.registryValue('domain'):
                irc.reply('Error: Your id is not under the %s domain.' % self.registryValue('domain'))
            else:
                irc.reply("Error: Invalid email")

    gchatemail = wrap(setemail, ['user', optional('otherUser'), 'something'])


    def addAlias(self, irc, msg, origuser, user, alias, config):
        if not config.has_section('Users'):
            config.add_section('Users')
        atest = self.aliasExists(alias, config)
        if atest and atest != user.name.lower():
            if atest == alias:
                irc.reply("You can not have an alias that is the name of a user.")
                return False
            irc.reply("%s already owns %s" % (atest,alias))
            return False
        elif atest:
            if atest == alias:
                irc.reply("Why are you trying to have an alias that is your name?")
                return False
            # irc.reply("Error: You already own that alias")
            irc.reply("Your aliases: %s" % ", ".join(aliases))
            return False
        aliases = config.get('Users', user.name).split(" ")
        if alias in aliases:
             # We should never reach here
            return False
        config.set('Users', user.name, " ".join(aliases) + " " + alias)
        aliases = aliases[1:]
        aliases.append(alias)
        log.info(str(aliases))
        if origuser.name == user.name:
            irc.reply("Your aliases: %s" % ", ".join(aliases))
        else:
            irc.reply("%s's aliases: %s" % (user.name, ", ".join(aliases)))
        return config
    def removeAlias(self, irc, msg, origuser, user, alias, config):
        if not config.has_section('Users'):
            config.add_section('Users')
        atest = self.aliasExists(alias, config)
        log.info('atest %s, user %s' % (atest, user.name))
        if atest and atest == user.name:
            if atest == alias:
                irc.reply("Error: You cannot remove yourself from the list. (yet)")
                return False
            aliases = config.get('Users', user.name).split(" ")
            aliases.pop(aliases.index(alias))
            if origuser.name == user.name:
                irc.reply("Your aliases: %s" % ", ".join(aliases[1:]))
            else:
                irc.reply("%s's aliases: %s" % (user.name, ", ".join(aliases[1:])))
        else:
            irc.replyError()
            return False
        if alias in aliases:
             # We should never reach here
            return False
        config.set('Users', user.name, " ".join(aliases))
        return config
    def setalias(self, irc, msg, args, user, otheruser, alias):
        """(<user>) <alias>
        Set the alias for your account. Prefix your alias with a dash (-) to signify that
        you would like that alias to be removed.
        """
        tmpUser = user
        if otheruser is not None and (user._checkCapability('owner') or otheruser is user):
            #irc.reply("ou %s alias %s" % (otheruser, alias))
            tmpUser = otheruser
        elif otheruser is not None and not user._checkCapability('owner'):
            irc.reply('Error: You are not authorized to add an alias to another user')
            return
        # if tmpUser == None:
        #     irc.reply('You need to specify a valid user before you can run this command')
        #     return
        # if irc.isChannel(msg.args[0]):
        #     raise callbacks.Error, conf.supybot.replies.requiresPrivacy()
        try:
            with self.touchOpen(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'), 'r+') as fp:
                config = ConfigParser.ConfigParser()
                config.readfp(fp)
                if alias[0] == '-':
                    result = self.removeAlias(irc, msg, user, tmpUser, alias[1:], config)
                else:
                    result = self.addAlias(irc, msg, user, tmpUser, alias.lower(), config)
                if not result:
                    fp.close()
                    return
                else:
                    config = result
                fp.truncate()
                fp.seek(0)
                config.write(fp)
                fp.truncate()
                fp.close()
        except Exception, e:
            if type(e) == ConfigParser.NoOptionError:
                irc.reply("Error: You need to set your email first with the \"%ssetemail <email>\" command..." % conf.supybot.reply.whenAddressedBy.chars())
                log.error('%s tried to set an alias when they didn\'t have an email set' % user.name)
                return
            log.error(str(e)) # log.error(str(traceback.print_tb(sys.exc_info()[2])))
            irc.replyError("Error: Failed to save your alias to the config file.")
    gchatalias = wrap(setalias, ['user', optional('otherUser'), 'something'])

    def tellall(self, irc, msg, args, autheduser, message):
        if not (self.registryValue('telleveryone') or autheduser._checkCapability('owner')):
            irc.reply("I'm sorry, but this command is currently disabled...")
            return
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'))
        if not config.has_section('Users'):
            config.add_section('Users')
        tmp = config.options('Users')
        # TODO - use this method for sending things
        # users = []
        # for name in tmp:
        #     email = config.get('Users', name)
        #     users.append((name,email.split(" ")[:1]))
        if users:
            calledUsers = []
            for user in users:
                message2 = "%s: %s" % (msg.nick, message)
                # status = self.sendEmail(irc, msg.nick, user[0], message2)
                status = self.sendEmail(irc, msg.nick, user, message2)
                if status != 0:
                    calledUsers.append(user)
            if calledUsers:
                irc.reply("Failed to send your message to: %s" % ", ".join(users))
            else:
                irc.reply("Your message has been successfully sent to everyone!")
        else:
            irc.replyError()
    gchattellall = wrap(tellall, ['user', 'text'])

    def aliasExists(self, alias, config):
        if not config.has_section('Users'):
            config.add_section('Users')
        names = config.has_option('Users', alias)
        if names:
            return alias
        names = config.options('Users')
        for name in names:
            aliases = config.get('Users', name).split(" ")
            if alias in aliases:
                return name
        return False

    def sendmessage(self, irc, msg, args, user, message):
        """<user> <Message>
        Send a <Message> to <user>
        """
        #print user + " -- " + repr(message)
        oldmsg = message
        message = msg.nick + ': ' + message
        status = self.sendEmail(irc, msg.nick, user.name, message)
        if status == 0:
            irc.replySuccess()
        elif status == 1:
            irc.reply("Error: Failed to send IM, User has not set their email address", prefixNick=False)
        elif status > 1:
            irc.replyError('Connection error: please try again in a few minutes.');
    gchatmessage = wrap(sendmessage, ['otherUser', 'text'])
    gchatmsg = wrap(sendmessage, ['otherUser', 'text'])

    def listusers(self, irc, msg, args):
        """
        List all of the users who have set up notifications.
        """
        channel = msg.args[0]
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'))
        if not config.has_section('Users'):
            config.add_section('Users')
        users = config.options('Users')
        if users:
            irc.reply('Users: %s' % ', '.join(users))
        else:
            irc.reply('Error: No users found.')
    gchatlistusers = wrap(listusers)

    def listaliases(self, irc, msg, args, user):
        """<user>
        List all of the aliases assigned to <user>.
        """
        channel = msg.args[0]
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'))
        if not config.has_section('Users'):
            config.add_section('Users')
        tmp = config.options('Users')
        try:
            aliases = config.get('Users', user.lower()).split(' ')
            aliases.pop(0)
            if aliases:
                irc.reply('Aliases: %s' % ', '.join(aliases))
            else:
                irc.reply('Error: No aliases found for %s.' % user)
        except Exception, e:
            log.error(str(e))
            irc.error('No user with that name exists in my records.')
    gchatlist = wrap(listaliases, ['something'])

    def nickSnarfer(self, irc, msg, match):
        r'(.*)'
        channel = msg.args[0]
        if(msg.nick.lower().endswith('bot') or not irc.isChannel(channel) or not self.registryValue('nickSnarfer', channel) or msg.args[1].startswith(conf.supybot.reply.whenAddressedBy.chars())):
            return
        def findWord(w):
            return re.compile(r'\b({0})\b'.format(w), flags=re.I).search
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'))
        if not config.has_section('Users'):
            config.add_section('Users')
        tmp = config.options('Users')
        users = tmp[:]
        for name in tmp:
            aliases = config.get('Users', name).split(" ")
            aliases.pop(0)
            users.extend(aliases)
        message = match.group(0).lower()
        calledNicks = {}
        for key in users:
            nick = findWord(key)(message)
            # if nick:
            #     log.info(str(key)+" "+self.aliasExists(nick.group(0), config))
            if nick and not self.aliasExists(nick.group(0), config) in irc.state.channels[channel].users and not self.aliasExists(nick.group(0), config) in calledNicks:
                # log.info(str(calledNicks))
                message2 = "%s.%s: %s" % (msg.nick, msg.args[0], msg.args[1])
                calledNicks[self.aliasExists(nick.group(0), config)] = self.sendEmail(irc, msg.nick, key, message2)
                #log.info(r'\\o/')
        users = []
        for nick, passed in calledNicks.iteritems():
            # log.info(str((nick,passed)))
            if passed == 0:
                users.append(nick)
        if users:
            users.sort()
            irc.reply('Notified %s' % ', '.join(users), prefixNick=False)
    nickSnarfer = urlSnarfer(nickSnarfer)

    def sendEmail(self, irc, suser, duser, message):
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(conf.supybot.directories.conf(), 'xmpp.conf'))
        # log.info(str(user))
        if not config.has_section('Users'):
            config.add_section('Users')
        alias = self.aliasExists(duser, config)
        # log.info('Alias %s exists. Owner: %s' % (duser,alias))
        if alias:
            email = config.get('Users', alias)
        else:
            email = None
        if email is not None:
            email = email.split(' ')[0]
            #subprocess.Popen(['python', '/.private/xmppScript/xmpp.py', '-t', email, '-m', message])
            # REPLACE - xmpp email id
            jid = xmpp.protocol.JID(self.registryValue('auth.username'))
            cl = xmpp.Client(jid.getDomain(), debug=[])
            connection = cl.connect(("talk.google.com", 5222))
            if connection:
                # REPLACE - xmpp password
                auth = cl.auth(jid.getNode(), self.registryValue('auth.password'), resource=jid.getResource())
                if auth:
                    id = cl.send(xmpp.protocol.Message(email, message))
                    cl.disconnect()
                    log.info('%s successfully sent a message to %s: %s' % (suser, duser, message))
                    return 0
                else:
                    log.error('XMPP: failed auth')
                    return 3
            else:
                log.error('XMPP: could not connect')
                return 2
        else:
            return 1


Class = XMPP


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:l
