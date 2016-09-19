import bottle
import requests
import beaker.middleware
from bottle import route, redirect, post, run, request, hook
from instagram import client, subscriptions

bottle.debug(True)

session_opts = {
    'session.type': 'file',
    'session.data_dir': './session/',
    'session.auto': True,
}

app = beaker.middleware.SessionMiddleware(bottle.app(), session_opts)

CONFIG = {
    'client_id': '04d8951caf16405ca00488b62e7c6251',#'1167b08cb87d493793cab23fe9b8882d',
    'client_secret': '3f57fbc9e6d34914a272997c1e93d801',#'1a22d617108a439c9ce8a3626b12ceb9',

    'redirect_uri': 'http://localhost:8515/oauth_callback'
}

unauthenticated_api = client.InstagramAPI(**CONFIG)

@hook('before_request')
def setup_request():
    request.session = request.environ['beaker.session']

def process_tag_update(update):
    print(update)

reactor = subscriptions.SubscriptionsReactor()
reactor.register_callback(subscriptions.SubscriptionType.TAG, process_tag_update)

@route('/')
def home():
    try:
        url = unauthenticated_api.get_authorize_url(scope=["likes","comments","public_content"])
        return '<a href="%s">Connect with Instagram</a>' % url
    except Exception as e:
        print(e)

def get_nav():
    nav_menu = ("<h1>Python Instagram</h1>"
                "<ul>"
                    "<li><a href='/recent'>User Recent Media</a> Calls user_recent_media - Get a list of a user's most recent media</li>"
                "</ul>")
    return nav_menu

@route('/oauth_callback')
def on_callback():
    code = request.GET.get("code")
    if not code:
        return 'Missing code'
    try:
        access_token, user_info = unauthenticated_api.exchange_code_for_access_token(code)
        if not access_token:
            return 'Could not get access token'
        api = client.InstagramAPI(access_token=access_token, client_secret=CONFIG['client_secret'])
        print(access_token)
        request.session['access_token'] = access_token
    except Exception as e:
        print(e)
    return get_nav()

@route('/recent')
def on_recent():
    content = "<h2>User Recent Media</h2>"
    access_token = request.session['access_token']
    if not access_token:
        return 'Missing Access Token'
    try:
        url = "https://api.instagram.com/v1/locations/165967/media/recent?access_token=" + access_token
        content += requests.get(url).content
    except Exception as e:
        print(e)
    return "%s %s" % (get_nav(),content)

bottle.run(app=app, host='localhost', port=8515, reloader=True)
