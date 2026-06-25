def validar_campos_vacios(campos):
    for campo, valor in campos.items():
        if tipo := (valor or '').strip() == '':
            return False, f"El campo '{campo}' no puede estar vacío"
    return True, ""
