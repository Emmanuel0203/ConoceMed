# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, TimeField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, InputRequired, Optional
from flask_wtf.file import FileField, MultipleFileField

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
        validators=[Optional()],  # Permitir valores nulos
        places=6
    )

    longitud = DecimalField(
        "Longitud",
        validators=[Optional()],  # Permitir valores nulos
        places=6
    )

    descripcion = TextAreaField(
        "Descripción",
        validators=[DataRequired(), Length(max=500)]
    )

    horario_apertura = TimeField(
        "Horario de apertura",
        validators=[Optional()],  # Permitir valores nulos
        format='%H:%M'
    )

    horario_cierre = TimeField(
        "Horario de cierre",
        validators=[Optional()],  # Permitir valores nulos
        format='%H:%M'
    )

    tarifa = DecimalField(
        "Tarifa de entrada",
        validators=[Optional(), NumberRange(min=0)],  # Permitir valores nulos
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

    archivos = MultipleFileField(
        "Subir Archivos",
        validators=[Optional()]  # Permitir valores nulos
    )

    submit = SubmitField("Enviar sugerencia")
