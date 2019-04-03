from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField
from wtforms.validators import URL
from flask_wtf.html5 import URLField

from pillar.web.utils.forms import FileSelectField


class FilmProjectForm(FlaskForm):
    video_url = URLField(validators=[URL()])
    picture_16_9 = FileSelectField('Picture 16x9', file_format='image')
    poster = FileSelectField('Poster Image', file_format='image')
    logo = FileSelectField('Logo', file_format='image')
    is_in_production = BooleanField('In Production')
    is_featured = BooleanField('Featured')
    theme_color = StringField('Theme Color')