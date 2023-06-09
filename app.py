# Khasan Rashidov April, 2023
# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json  # to handle JSON objects
import logging  # to log errors
import sys  # to handle errors
from datetime import datetime  # to work with datetime objects
from logging import FileHandler, Formatter  # to log errors

import babel  # to format dates
import dateutil.parser  # to parse datetime strings
from flask import (Flask,  # to create and configure the app
                   Response,  # to handle responses
                   abort,  # to handle errors
                   flash,  # to display messages
                   jsonify,  # to handle JSON objects
                   redirect,  # to redirect users
                   render_template,  # to render templates
                   request,  # to handle requests
                   url_for)  # to generate URLs
from flask_migrate import Migrate  # to run migrations
from flask_moment import Moment  # to format dates
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm as Form  # to create forms
from flask_wtf.csrf import CSRFProtect   # to protect against CSRF attacks

from config import SQLALCHEMY_DATABASE_URI
from forms import *
from models import Artist, Show, Venue, db

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

# config
app = Flask(__name__)
app.config.from_object('config')

moment = Moment(app)
db.init_app(app)  # to connect to a local postgresql database

migrate = Migrate(app, db)  # to run migrations

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    recent_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    return render_template('pages/home.html',
                           recent_artists=recent_artists,
                           recent_venues=recent_venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated
    # based on number of upcoming shows per venue.
    data = []
    areas = db.session.query(Venue.city, Venue.state).distinct().all()
    for area in areas:
        venues = Venue.query.filter_by(
            city=area.city).filter_by(state=area.state).all()
        venue_data = []
        for venue in venues:
            venue_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(venue.shows)
            })
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venue_data
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists
    # with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should
    # return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    response = {
        "count": len(venues),
        "data": venues
    }

    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    # The code joins tables from existing models
    # to select Artists by Venues where they previously performed,
    # successfully filling out
    # the Venues page with a “Past Performances” section.
    past_shows = db.session.query(Artist, Show).join(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.artist_id == Artist.id). \
        filter(Show.start_time < datetime.now()).all()
    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue). \
        filter(Show.venue_id == venue_id). \
        filter(Show.artist_id == Artist.id).filter(
            Show.start_time > datetime.now()).all()
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [{
            "artist_id": show.Artist.id,
            "artist_name": show.Artist.name,
            "artist_image_link": show.Artist.image_link,
            "start_time": str(show.Show.start_time)
        } for show in past_shows],
        "upcoming_shows": [{
            "artist_id": show.Artist.id,
            "artist_name": show.Artist.name,
            "artist_image_link": show.Artist.image_link,
            "start_time": str(show.Show.start_time)
        } for show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()  # instantiate the form

    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    # csrf=False to avoid csrf token error
    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
            )
            db.session.add(venue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
            return render_template('pages/home.html')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')
            return render_template('pages/home.html')
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(field + ' ' + error)
        flash('Errors ' + str(message))
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record.
    # Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except Exception:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

    # BONUS CHALLENGE:
    # Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db
    # then redirect the user to the homepage
    return None

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.order_by('id').all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. .
    # Ensure it is case-insensitive.
    # seach for "A" should return
    # "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term')
    artist = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
    response = {
        "count": len(artist),
        "data": artist
    }

    return render_template('pages/search_artists.html',
                           results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO:
    # replace with real artist data from the artist table, using artist_id
    # The code joins tables from existing models
    # to successfully fill out the Artists page
    # with a “Venues Performed” section.
    artist = Artist.query.get(artist_id)
    past_shows = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).\
        filter(Show.start_time < datetime.now()).all()
    upcoming_shows = db.session.query(Show).join(Venue).\
        filter(Show.artist_id == artist_id).\
        filter(Show.start_time > datetime.now()).all()

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": json.loads(artist.genres),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [{
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        } for show in past_shows],
        "upcoming_shows": [{
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        } for show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template('pages/show_artist.html', artist=data)

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    form = ArtistForm()

    # TODO: populate form with fields from artist with ID <artist_id>
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.image_link.data = artist.image_link
    form.genres.data = json.loads(artist.genres)

    return render_template('forms/edit_artist.html',
                           form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.facebook_link = form.facebook_link.data
            artist.website = form.website.data
            artist.image_link = form.image_link.data
            artist.genres = json.dumps(form.genres.data)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully updated!')
            return redirect(url_for('show_artist',
                                    artist_id=artist_id))
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be updated.')
            return redirect(url_for('edit_artist',
                                    artist_id=artist_id))
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(field + ' ' + error)
        flash('Errors ' + str(message))
        return redirect(url_for('edit_artist',
                                artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.filter_by(id=venue_id).first()
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.facebook_link.data = venue.facebook_link
    form.website.data = venue.website
    form.image_link.data = venue.image_link
    form.genres.data = json.loads(venue.genres)

    return render_template('forms/edit_venue.html',
                           form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.facebook_link = form.facebook_link.data
            venue.website = form.website.data
            venue.image_link = form.image_link.data
            venue.genres = json.dumps(form.genres.data)
            db.session.commit()
            flash('Venue ' + request.form['name'] +
                  ' was successfully updated!')
            return redirect(url_for('show_venue',
                                    venue_id=venue_id))
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
            return redirect(url_for('edit_venue',
                                    venue_id=venue_id))
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(field + ' ' + error)
        flash('Errors ' + str(message))
        return redirect(url_for('edit_venue',
                                venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html',
                           form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    # meta={'csrf': False} to disable csrf token
    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            artist = Artist(name=form.name.data,
                            city=form.city.data,
                            state=form.state.data,
                            phone=form.phone.data,
                            facebook_link=form.facebook_link.data,
                            website=form.website.data,
                            image_link=form.image_link.data,
                            genres=json.dumps(form.genres.data),
                            seeking_venue=form.seeking_venue.data,
                            seeking_description=form.seeking_description.data)
            db.session.add(artist)
            db.session.commit()
            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
            return render_template('pages/home.html')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
            return render_template('pages/home.html')
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(field + ' ' + error)
        flash('Errors ' + str(message))
        return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.all()
    data = []
    for attribute in shows:
        item = ({
            "venue_id": attribute.Venue.id,
            "venue_name": attribute.Venue.name,
            "artist_id": attribute.Artist.id,
            "artist_name": attribute.Artist.name,
            "artist_image_link": attribute.Artist.image_link,
            "start_time": attribute.Show.date.strftime("%Y-%m-%d %H:%M:%S")
        })
        data.append(item)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db,
    # upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form, meta={'csrf': False})
    if form.validate():
        try:
            show = Show(artist_id=form.artist_id.data,
                        venue_id=form.venue_id.data,
                        date=form.start_time.data)
            db.session.add(show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
            return render_template('pages/home.html')
        except Exception:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Show could not be listed.')
            return redirect(url_for('create_shows'))
        finally:
            db.session.close()
    else:
        message = []
        for field, errors in form.errors.items():
            for error in errors:
                message.append(field + ' ' + error)
        flash('Errors ' + str(message))
        return redirect(url_for('create_shows'))

    # # on successful db insert, flash success
    # flash('Show was successfully listed!')
    # # TODO: on unsuccessful db insert, flash an error instead.
    # # e.g., flash('An error occurred. Show could not be listed.')
    # # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    # return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.debug = True
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
