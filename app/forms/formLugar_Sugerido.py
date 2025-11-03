from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class LugarSugeridoForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=200)])
    direccion = StringField("Dirección", validators=[DataRequired()])
    latitud = DecimalField("Latitud", places=7, validators=[DataRequired(), NumberRange(-90, 90)])
    longitud = DecimalField("Longitud", places=7, validators=[DataRequired(), NumberRange(-180, 180)])
    descripcion = TextAreaField("Descripción", validators=[DataRequired()])
    submit = SubmitField("Enviar sugerencia")
