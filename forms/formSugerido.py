# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, TimeField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, InputRequired

class LugarSugeridoForm(FlaskForm):
    """Formulario para sugerir un nuevo lugar."""

    nombre = StringField(
        "Nombre del lugar",
        validators=[DataRequired(), Length(max=100)]
    )

    direccion = StringField(
        "Dirección",
        validators=[DataRequired(), Length(max=200)]
    )

    latitud = DecimalField(
        "Latitud",
        validators=[DataRequired()],
        places=6
    )

    longitud = DecimalField(
        "Longitud",
        validators=[DataRequired()],
        places=6
    )

    descripcion = TextAreaField(
        "Descripción",
        validators=[DataRequired(), Length(max=500)]
    )

    horario_apertura = TimeField(
        "Horario de apertura",
        validators=[DataRequired()],
        format='%H:%M'
    )

    horario_cierre = TimeField(
        "Horario de cierre",
        validators=[DataRequired()],
        format='%H:%M'
    )

    tarifa = DecimalField(
        "Tarifa de entrada",
        validators=[InputRequired(), NumberRange(min=0)],
        places=2
    )
    

    # 👇 Este campo será llenado dinámicamente desde la vista
    idLocalidad = SelectField(
        "Localidad",
        choices=[],  # ← se rellenará desde la vista
        validators=[DataRequired()]
    )

    idCategoria_Turistica = SelectField(
        "Categoría Turística",
        choices=[],  # Se llenará dinámicamente desde la vista
        validators=[DataRequired()]
    )

    submit = SubmitField("Enviar sugerencia")
