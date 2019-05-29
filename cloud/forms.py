from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField
from wtforms.fields.html5 import URLField
from wtforms.validators import URL

from pillar.web.utils.forms import FileSelectField


class FilmProjectForm(FlaskForm):
    video_url = URLField(validators=[URL()])
    poster = FileSelectField('Poster Image', file_format='image')
    logo = FileSelectField('Logo', file_format='image')
    is_in_production = BooleanField('In Production')
    is_featured = BooleanField('Featured')
    theme_color = StringField('Theme Color')
