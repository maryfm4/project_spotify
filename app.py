import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from flask import Flask, session, request, redirect, url_for, render_template
from flask_session import Session
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session'
Session(app)

# Wygeneruj własne id i secret
# client_id = ""
# client_secret = ""
redirect_uri = 'http://localhost:5000/callback'
scope = 'user-top-read, user-read-currently-playing, playlist-modify-private, playlist-modify-public'

# Autoryzacja czy klient jest zalogowany oraz wyraził zgodę na wszystkie wymagane pobrane dane i generowanie tokenu.


@app.route('/')
def homepage():
    # Obiekt zarządzający sesją użytkownika i przechowuje informacje o tokenie we Flasku.
    cache_handler = FlaskSessionCacheHandler(session)

    oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope,
                         cache_handler=cache_handler, show_dialog=True)
    if not oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_tracks_and_artists'))

# Odświeżanie tokenów i automatyczne 'czyszczenie' zapisanej bazy danych i przekierowanie ponowne do procesu autoryzacji


@app.route('/callback')
def callback():
    # Obiekt zarządzający sesją użytkownika bez sprawdzania pamięci podręcznej przed generowaniem tokenów.
    cache_handler = FlaskSessionCacheHandler(session)

    oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope,
                         cache_handler=cache_handler, show_dialog=True)
    oauth.get_access_token(request.args['code'], check_cache=False)
    return redirect(url_for('get_tracks_and_artists'))


# Pobranie top 50 piosenek i 10 artystów na przełomie zbierania danych przez spotify (po wrraped)


@app.route('/get_tracks_and_artists')
def get_tracks_and_artists():
    global tracks_info
    cache_handler = FlaskSessionCacheHandler(session)

    oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope,
                         cache_handler=cache_handler, show_dialog=True)
    if not oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return redirect(auth_url)
    sp_client = Spotify(auth_manager=oauth)

    tracks = sp_client.current_user_top_tracks(limit=50, offset=1, time_range='long_term')
    artists = sp_client.current_user_top_artists(limit=10, offset=0, time_range='long_term')
    tracks_info = [(i['name']) for i in tracks['items']]
    artists_info = [(i['name']) for i in artists['items']]
    return render_template('base.html', tracks=tracks_info, artists=artists_info)


# Przekazywanie danych piosenek i automatyczne tworzenie playlisty dla zalogoqwanego użytkownika

@app.route('/create_playlist')
def create_playlist():
    cache_handler = FlaskSessionCacheHandler(session)

    oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope,
                         cache_handler=cache_handler, show_dialog=True)
    if not oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return redirect(auth_url)
    sp_client = Spotify(auth_manager=oauth)
    tracks = sp_client.current_user_top_tracks(limit=50, offset=0, time_range='long_term')
    track_id = [track['id'] for track in tracks['items']]
    user_id = sp_client.current_user()['id']

    playlist = (sp_client.user_playlist_create(user=user_id, name='Top tracks', public=True, collaborative=False,
                                               description='Top tracks'
                                                           'of the year'))
    playlist_id = playlist['id']
    print(playlist_id)
    sp_client.playlist_add_items(playlist_id, track_id)
    return render_template('base1.html', playlistid=playlist_id)


# Możliwość ręcznego wylogowania i wyczyszczenia sesji.

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))


if __name__ == '__main__':
    app.run(debug=True)
