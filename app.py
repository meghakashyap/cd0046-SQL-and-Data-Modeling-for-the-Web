#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import desc, func
from forms import *
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Models are update in models.py
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    
    genres = db.Column(db.ARRAY(db.String),nullable=False) 
    website = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description =db.Column(db.String(700))
    past_shows_count = db.Column(db.Integer,default=0)
    upcoming_shows_count = db.Column(db.Integer,default=0)
    show = db.relationship('Show',backref='venue',lazy=True, cascade='all')

   

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean,default=False)
    seeking_description = db.Column(db.String(700))
    past_shows_count = db.Column(db.Integer,default=0)
    upcoming_shows_count = db.Column(db.Integer,default=0)
    show = db.relationship('Show',backref='artist',lazy=True)
   



  

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer,primary_key=True)
  start_time = db.Column(db.DateTime,nullable=False)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id'),nullable=False)
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id'),nullable=False)
  upcoming_show = db.Column(db.Boolean,default=True)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues=  Venue.query.order_by(desc(Venue.id)).limit(10).all()
  artists=  Artist.query.order_by(desc(Artist.id)).limit(10).all()
  return render_template('pages/home.html',artists=artists ,venues=venues)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data =[]
  venue_list = (Venue.query.with_entities(func.count(Venue.id),Venue.city,Venue.state).group_by(Venue.city,Venue.state).all())
  
  for place in venue_list:
    venue_place =(
      Venue.query.filter_by(state=place.state)
            .filter_by(city=place.city)
            .all()
    )
    venue_info =[]
    num_upcoming_shows =(
       db.session.query(Show)
            .filter(Show.venue_id == 1)
            .filter(Show.start_time > datetime.now())
            .all()
      # db.session.query(Show).filter_by(Show.venue_id==1).filter_by(Show.start_time>datetime.now()).all()
    )
    for venue in venue_place:
      venue_info.append({
        "id":venue.id,
        "name":venue.name,
        "num_upcoming_shows":len(num_upcoming_shows),
      }
      )
    data.append({
      "city":place.city,"state":place.state,"venues": venue_info })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_text = request.form.get('search_term')
  search_results = Venue.query.filter(
        Venue.name.ilike("%{}%".format(search_text))
    ).all()
  data = []
  for venue in search_results:
    num_upcoming_shows =(
      db.session.query(Show)
      .filter(Show.venue_id == venue.id)
      .filter(Show.start_time>datetime.now())
      .all()
    )
    data.append(
      {
        "id":venue.id,
        "name":venue.name,
        "num_upcoming_shows":len(num_upcoming_shows)
      }
    )
  response = {
      "count": len(search_results),
      "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ""))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  past_shows =[]
  upcoming_shows=[]
  current_time = datetime.now()
  
  upcoming_shows_list =(
    db.session.query(Show)
    .join(Artist)
    .filter(Show.venue_id==venue_id)
    .filter(Show.start_time>current_time)
    .all()
  )
  past_shows_list =(
    db.session.query(Show)
    .join(Artist)
    .filter(Show.venue_id==venue_id)
    .filter(Show.start_time<current_time)
    .all()
  )
  for past_show in past_shows_list:
    past_shows.append({
      "artist_id":past_show.artist_id,
      "artist_name":past_show.artist.name,
      "artist_image_link":past_show.artist.image_link,
      "start_time":str(past_show.start_time),
    })
  for upcoming_show in upcoming_shows_list:
    upcoming_shows.append({
      "artist_id":upcoming_show.artist_id,
      "artist_name":upcoming_show.artist.name,
      "artist_image_link":upcoming_show.artist.image_link,
      "start_time":str(upcoming_show.start_time),
    })

  data={
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
    "image_link": venue.image_link ,
    "past_shows": past_shows,
    "upcoming_shows":upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)



@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf':False})
  error =False
  if form.validate():
    try:
      new_venue=Venue(
        name=form.name.data,
        city=form.city.data,
        state= form.state.data,
        address= form.address.data,
        phone =form.phone.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        genres=form.genres.data,
        website=form.website_link.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description=form.seeking_description.data,    
      )
      db.session.add(new_venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
      print(e)
      db.session.rollback()
      print(sys.exc_info())
      flash(
        "An error has occured. Venue"+ new_venue.name+" Could not listed in Venue."
      )
      error=True
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else:
    message=[]
    for field,errors in form.errors.items():
      for error in errors:
        message.append(f"{field}:{error}")
    flash("Please fix the showing error: "+",".join(message))
    form = VenueForm()
    return render_template('pages/home.html',form=form)
    

@app.route('/venues/<int:venue_id>/delete')
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash("Venue has deleted successfully !")

  except Exception as e:
    db.session.rollback()
    print(sys.exc_info())
    print(str(e))
    flash("An error has occured could not deleted !")
  finally:
    db.session.close()
  return render_template('pages/home.html')
 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  search_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []
  for artist in search_results:
    num_upcoming_shows =(
      db.session.query(Artist)
      .filter(Artist.name.ilike(f'%{search_term}%')).all()
    )
    data.append(
      {
        "id":artist.id,
        "name":artist.name,
        "num_upcoming_shows":len(num_upcoming_shows),
      }
    )
  response = {
      "count": len(search_results),
      "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  past_shows=[]
  upcoming_shows=[]
  current_time= datetime.now()
  
  upcoming_show_list=(
    db.session.query(Show)
    .join(Venue)
    .filter(Show.artist_id==artist_id)
    .filter(Show.start_time>current_time).all()
  )
  
  past_show_list=(
    db.session.query(Show)
    .join(Venue)
    .filter(Show.artist_id==artist_id)
    .filter(Show.start_time<current_time).all()
  )
  
  for past_show in past_show_list:
    past_shows.append(
      {
      "venue_id": past_show.venue_id,
      "venue_name": past_show.venue.name,
      "venue_image_link": past_show.venue.image_link,
      "start_time": str(past_show.start_time)
      }
    )
    
  for upcoming_show in upcoming_show_list:
    upcoming_shows.append(
      {
      "venue_id": upcoming_show.venue_id,
      "venue_name": upcoming_show.venue.name,
      "venue_image_link": upcoming_show.venue.image_link,
      "start_time": str(upcoming_show.start_time)
      }
    )
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(request.form)
  form.populate_obj(artist)
  try:
    db.session.commit()
    flash("Artist"+artist.name+"is updated successfully !")
  except Exception as e:
    db.session.rollback()
    print(sys.exc_info()[1])
    print(e)
    flash("Artist"+artist.name+"is not updated successfully due "+e)
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(request.form)
  if request.method=='POST':
    form.populate_obj(venue)
    try:
      db.session.commit()
      flash("Venue "+ venue.name+" has updated successfully !")
    except Exception as e:
      db.session.rollback()
      print(sys.exc_info())
      flash("Venue "+ venue.name+" not updated successfully !")
    finally:
      db.session.close()
  else:
    flash("Venue "+ venue.name+" not updated successfully !")
    print(form.errors)
  print('request.form.get("name"): ' + form.name.data)
  return redirect(url_for('show_venue', form=form, venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta={'csrf':False})
  if form.validate():
    try:
      new_artist= Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=form.genres.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        website=form.website_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data,
      )
      db.session.add(new_artist)
      db.session.commit()
    # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
      print(e)
      db.seesion.rollback()
      print(sys.exc_info())
      flash( "An error occurred. Artist " + new_artist.name + " could not be listed.")
    finally:
      db.session.close()
      return render_template('pages/home.html')
  else:
    message=[]
    for field, errors in form.errors.items():
      for error in errors:
        message.append('f{field}:{error}')
    flash("Please fix the following errors: " + ", ".join(message))
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)

 
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  show_all = Show.query.all()
  data=[]
  for show in show_all:
    artist = Artist.query.get(show.artist_id)
    venue = Venue.query.get(show.venue_id)
    if show.upcoming_show:
      data.append({
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time),
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form, meta={'csrf':False})
  if form.validate():
    try:
      new_show= Show(
        venue_id= form.venue_id.data,
        artist_id= form.artist_id.data,
        start_time= form.start_time.data
        )
      
      db.session.add(new_show)
      db.session.commit()
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except Exception as e:
      print(e)
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
      print(sys.exc_info())
    finally:
      db.session.close()
    return render_template('pages/home.html')
  else:
    message=[]
    for field, errors in form.errors.items():
      for error in errors:
        message.append('f{field}:{error}')
    flash("Please fix the following errors: " + ", ".join(message))
    form = ShowForm()
    return render_template('pages/new_show.html', form=form)
  

  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", debug=True)