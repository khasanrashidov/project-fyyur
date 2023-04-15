from datetime import datetime
from flask_wtf import FlaskForm as Form
from wtforms import StringField, \
    SelectField, \
    SelectMultipleField, \
    DateTimeField, \
    BooleanField
from wtforms.validators import DataRequired, \
    AnyOf, \
    URL, \
    Regexp, \
    Optional
from flask_wtf.csrf import CSRFProtect
from flask import Flask
import re  # regular expressions for phone number validation
from enums import Genre, State


app = Flask(__name__)
csrf = CSRFProtect(app)

# state_choices = [
#     ('AL', 'AL'),
#     ('AK', 'AK'),
#     ('AZ', 'AZ'),
#     ('AR', 'AR'),
#     ('CA', 'CA'),
#     ('CO', 'CO'),
#     ('CT', 'CT'),
#     ('DE', 'DE'),
#     ('DC', 'DC'),
#     ('FL', 'FL'),
#     ('GA', 'GA'),
#     ('HI', 'HI'),
#     ('ID', 'ID'),
#     ('IL', 'IL'),
#     ('IN', 'IN'),
#     ('IA', 'IA'),
#     ('KS', 'KS'),
#     ('KY', 'KY'),
#     ('LA', 'LA'),
#     ('ME', 'ME'),
#     ('MT', 'MT'),
#     ('NE', 'NE'),
#     ('NV', 'NV'),
#     ('NH', 'NH'),
#     ('NJ', 'NJ'),
#     ('NM', 'NM'),
#     ('NY', 'NY'),
#     ('NC', 'NC'),
#     ('ND', 'ND'),
#     ('OH', 'OH'),
#     ('OK', 'OK'),
#     ('OR', 'OR'),
#     ('MD', 'MD'),
#     ('MA', 'MA'),
#     ('MI', 'MI'),
#     ('MN', 'MN'),
#     ('MS', 'MS'),
#     ('MO', 'MO'),
#     ('PA', 'PA'),
#     ('RI', 'RI'),
#     ('SC', 'SC'),
#     ('SD', 'SD'),
#     ('TN', 'TN'),
#     ('TX', 'TX'),
#     ('UT', 'UT'),
#     ('VT', 'VT'),
#     ('VA', 'VA'),
#     ('WA', 'WA'),
#     ('WV', 'WV'),
#     ('WI', 'WI'),
#     ('WY', 'WY'),
# ]

# genre_choices = [
#     ('Alternative', 'Alternative'),
#     ('Blues', 'Blues'),
#     ('Classical', 'Classical'),
#     ('Country', 'Country'),
#     ('Electronic', 'Electronic'),
#     ('Folk', 'Folk'),
#     ('Funk', 'Funk'),
#     ('Hip-Hop', 'Hip-Hop'),
#     ('Heavy Metal', 'Heavy Metal'),
#     ('Instrumental', 'Instrumental'),
#     ('Jazz', 'Jazz'),
#     ('Musical Theatre', 'Musical Theatre'),
#     ('Pop', 'Pop'),
#     ('Punk', 'Punk'),
#     ('R&B', 'R&B'),
#     ('Reggae', 'Reggae'),
#     ('Rock n Roll', 'Rock n Roll'),
#     ('Soul', 'Soul'),
#     ('Other', 'Other'),
# ]


def is_valid_phone(number):
    """ Validate phone numbers like:
    1234567890 - no space
    123.456.7890 - dot separator
    123-456-7890 - dash separator
    123 456 7890 - space separator

    Patterns:
    000 = [0-9]{3}
    0000 = [0-9]{4}
    -.  = ?[-. ]

    Note: (? = optional) - Learn more: https://regex101.com/
    """
    pattern = re.compile(r'^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$')
    return pattern.match(number)


class ShowForm(Form):
    artist_id = StringField(
        'artist_id',
        validators=[DataRequired(), Regexp(
            '^[0-9]*$', message='Artist ID must be a number')]
    )
    venue_id = StringField(
        'venue_id',
        validators=[DataRequired(), Regexp(
            '^[0-9]*$', message='Venue ID must be a number')]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default=datetime.today()
    )


class VenueForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices(),
        validate_choice=False,  # disable validation for choices
    )
    address = StringField(
        'address', validators=[DataRequired()]
    )
    phone = StringField(
        'phone'
    )
    image_link = StringField(
        'image_link', validators=[URL()]  # URL validator
    )
    genres = SelectMultipleField(
        # TODO implement enum restriction
        'genres', validators=[DataRequired()],
        choices=Genre.choices(),
        validate_choice=False,  # disable validation for choices
    )
    facebook_link = StringField(
        # URL validator, Optional() to allow empty string
        'facebook_link', validators=[Optional(), URL()]
    )
    website_link = StringField(
        'website_link',
        # URL validator, Optional() to allow empty string
        validators=[Optional(), URL()]
    )

    seeking_talent = BooleanField('seeking_talent')

    seeking_description = StringField(
        'seeking_description'
    )

    def validate(self, **kwargs):
        # `**kwargs` to match the method's signature in the `FlaskForm` class.
        """Define a custom validate method in your Form:"""
        validated = Form.validate(self)
        if not validated:
            return False

        # Validate phone number
        if self.phone.data and not is_valid_phone(self.phone.data):
            self.phone.errors.append('Invalid phone number')
            return False

        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append('Invalid genre')
            return False

        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append('Invalid state')
            return False

        return True  # all validations passed


class ArtistForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices(),
        validate_choice=False,  # disable validation for choices
    )
    phone = StringField(
        # TODO implement validation logic for state
        'phone'
    )
    image_link = StringField(
        'image_link',
        validators=[URL()]  # URL validator
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genre.choices(),
        validate_choice=False,  # disable validation for choices
    )
    facebook_link = StringField(
        # TODO implement enum restriction
        # URL validator, Optional() to allow empty string
        'facebook_link', validators=[URL(), Optional()]
    )

    website_link = StringField(
        # URL validator, Optional() to allow empty string
        'website_link', validators=[URL(), Optional()]
    )

    seeking_venue = BooleanField('seeking_venue')

    seeking_description = StringField(
        'seeking_description'
    )

    def validate(self, **kwargs):
        # `**kwargs` to match the method's signature in the `FlaskForm` class.
        """Define a custom validate method in your Form:"""
        validated = Form.validate(self)
        if not validated:
            return False

        # Validate phone number
        if self.phone.data and not is_valid_phone(self.phone.data):
            self.phone.errors.append('Invalid phone number')
            return False

        if not set(self.genres.data).issubset(dict(Genre.choices()).keys()):
            self.genres.errors.append('Invalid genre')
            return False

        if self.state.data not in dict(State.choices()).keys():
            self.state.errors.append('Invalid state')
            return False

        return True  # all validations passed
