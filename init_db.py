from database_manager_postgres import inicializar_base_datos

if __name__ == "__main__":
    print("Inicializando base de datos en producción...")
    if inicializar_base_datos():
        print("Base de datos lista")
    else:
        print("Error en inicialización")
        exit(1)