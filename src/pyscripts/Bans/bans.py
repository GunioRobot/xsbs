import sbserver
from xsbs.settings import PluginConfig
from xsbs.colors import red, colordict
from xsbs.ui import insufficientPermissions
from xsbs.events import triggerServerEvent, registerServerEventHandler, registerPolicyEventHandler, execLater
from xsbs.commands import registerCommandHandler
from DB.db import dbmanager
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
import time, string

Base = declarative_base()
session = dbmanager.session()

class Ban(Base):
	__tablename__='bans'
	id = Column(Integer, primary_key=True)
	ip = Column(Integer)
	expiration = Column(Integer) # Epoch seconds
	reason = Column(String)
	nick = Column(String)
	banner_ip = Column(Integer)
	banner_nick = Column(String)
	time = Column(Integer)
	def __init__(self, ip, expiration, reason, nick, banner_ip, banner_nick, time=time.time()):
		self.ip = ip
		self.expiration = expiration
		self.reason = reason
		self.nick = nick
		self.banner_ip = banner_ip
		self.banner_nick = banner_nick
		self.time = time
	def isExpired(self):
		return self.expiration <= time.time()


def getCurrentBanByIp(ipaddress):
	return session.query(Ban).filter(Ban.ip==ipaddress).filter('expiration>'+str(time.time())).one()

def isCurrentlyBanned(ipaddress):
	try:
		b = getCurrentBanByIp(ipaddress)
		return True
	except NoResultFound:
		return False

def ban(cn, seconds, reason, banner_cn):
	ip = sbserver.playerIpLong(cn)
	expiration = time.time() + seconds
	nick = sbserver.playerName(cn)
	if banner_cn != -1:
		banner_ip = sbserver.playerIpLong(banner_cn)
		banner_nick = sbserver.playerName(banner_cn)
	else:
		banner_ip = 0
		banner_nick = ''
	newban = Ban(ip, expiration, reason, nick, banner_ip, banner_nick)
	session.add(newban)
	session.commit()
	execLater(sbserver.playerKick, (cn,))

config = PluginConfig('bans')
ban_command = config.getOption('Config', 'ban_command', 'ban')
default_ban_length = config.getOption('Config', 'default_ban_time', 3600)
ban_message = config.getOption('Config', 'message', 'Banning $name for $seconds seconds for ${red}${reason}')
ban_message = string.Template(ban_message)
default_reason = config.getOption('Config', 'default_reason', 'unspecified reason')
del config

def onBanCmd(cn, text):
	sp = text.split(' ')
	try:
		if sbserver.playerPrivilege(cn) == 0:
			insufficientPermissions(cn)
			return
		tcn = int(sp[0])
		try:
			ip = sbserver.playerIpLong(tcn)
		except ValueEror:
			sbserver.playerMessage(cn, red('Invalid cn'))
			return
		reason = ''
		length = 0
		if len(sp) >= 3:
			reason = sp[2]
		else:
			reason = default_reason
		if len(sp) >= 2:
			length = int(sp[1])
		else:
			length = int(default_ban_length)
		ban(tcn, length, reason, cn)
	except (ValueError, KeyError):
		sbserver.playerMessage(cn, red('Usage: #ban <cn> (duration) (reason)'))

def allowClient(cn):
	ip = sbserver.playerIpLong(cn)
	return not isCurrentlyBanned(ip)

def onKick(tcn, cn):
	ban(tcn, 14500, 'Unspecified reason', cn)

def init():
	registerPolicyEventHandler("allow_connect", allowClient)
	registerCommandHandler('ban', onBanCmd)
	registerServerEventHandler('player_ban', ban)
	registerServerEventHandler('player_kicked', onKick)
	Base.metadata.create_all(dbmanager.engine)

init()
