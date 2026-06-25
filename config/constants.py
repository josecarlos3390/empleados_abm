"""
Configuración de opciones para listas desplegables
"""

# Motivos de desvinculación
MOTIVOS_DESVINCULACION = [
    '',  # Opción vacía por defecto
    '1. Droga',
    '2. Violencia Familiar',
    '3. Salud',
    '4. Problema Laboral',
    '5. Falsificación de Documentos y/o certificados',
    '6. Faltas injustificadas',
    '7. Robo o Hurto',
    '8. Bajo rendimiento',
    '9. Incumplimiento de funciones',
    '10. Negativa a seguir instrucciones',
    '11. Desobediencia reiterada',
    '12. Uso indebido de recursos',
    '13. Violación de políticas internas',
    '14. Conducta fraudulenta',
    '15. Inestabildiad Emocional',
    '16. Acoso laboral',
    '17. Conflictos con compañeros',
    '18. Actitud agresiva o desafiante',
    '19. Procesos legales abiertos contra la empresa u otras',
    '20. Desempeño extremadamente bajo o sabotaje'
    '21. Parentesco Familiar'
]

# Evaluaciones internas
EVALUACIONES_INTERNAS = [
    '',  # Opción vacía por defecto
    #'Excelente',
    #'Muy bueno',
    #'Bueno',
    #'Regular',
    #'Deficiente',
    #'No evaluado'
    '1. Grave',
    '2. Negativa',
    '3. Leve',
    '4. Moderado'
]

# Tamaño máximo de archivo (en bytes) - 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Extensiones de archivo permitidas
ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 
    'jpg', 'jpeg', 'png', 'gif',
    'txt', 'zip', 'rar'
}

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS