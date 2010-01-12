from xsbs.http import urlHandler, regexUrlHandler, isMaster
from xsbs.players import all as allClients, player, playerCount, spectatorCount
from xsbs.net import ipLongToString
import sbserver
import json

class jsonMasterRequired(object):
	def __init__(self, func):
		self.func = func
		self.__doc__ = func.__doc__
		self.__name__ = func.__name__
	def __call__(self, *args, **kwargs):
		try:
			username = args[0].body['username'][0]
			password = args[0].body['password'][0]
			ismaster = isMaster(username, password)
		except (AttributeError, KeyError):
			args[0].respond_with(200, 'text/plain', 0, json.dumps(
				{ 'error': 'INVALID_LOGIN' }))
		else:
			if ismaster:
				self.func(*args, **kwargs)
			else:
				args[0].respond_with(200, 'text/plain', 0, json.dumps(
					{ 'error': 'INVALID_LOGIN' }))

@urlHandler('/json/admin/set_map')
@jsonMasterRequired
def setMap(request):
	try:
		map = request.body['map'][0]
		mode = request.body['mode'][0]
		mode = int(mode)
	except (KeyError, IndexError):
		request.respond_with(200, 'text/plain', 0, json.dumps({
			'error': 'INVALID_PARAMS' }))
	else:
		request.respond_with(200, 'text/plain', 0, json.dumps({
			'result': 'SUCCESS' }))
		sbserver.setMap(map, mode)

@urlHandler('/json/game')
def game(request):
	request.respond_with(200, 'text/plain', 0, json.dumps({
		'map': sbserver.mapName(),
		'mode': sbserver.gameMode(),
		'players': playerCount(),
		'spectators': spectatorCount() }))

@urlHandler('/json/server')
def server(request):
	request.respond_with(200, 'text/plain', 0, json.dumps({
		'num_clients': sbserver.numClients(),
		'master_mode': sbserver.masterMode(),
		'uptime': sbserver.uptime() }))

@regexUrlHandler('/json/clients/(?P<cn>\d+)')
def clientDetail(request, cn):
	try:
		p = player(int(cn))
	except ValueError:
		response = { 'error': 'Invalid cn' }
	else:
		response = { 'cn': p.cn,
			'name': p.name(),
			'team': p.team(),
			'frags': p.frags(),
			'deaths': p.deaths(),
			'teamkills': p.teamkills(),
			'privilege': p.privilege() }
	request.respond_with(200, 'text/plain', 0, json.dumps(response))

@urlHandler('/json/clients')
def getClients(request):
	response = []
	for p in allClients():
		response.append( {
			'cn': p.cn,
			'name': p.name(),
			'team': p.team() } )
	request.respond_with(200, 'text/plain', 0, json.dumps(response))

