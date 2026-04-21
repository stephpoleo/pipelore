# cuántos chunks traer por pregunta — subir si las respuestas pierden contexto
TOP_K = 3

# distancia coseno máxima aceptada (0 = idéntico, 2 = opuesto)
# con Jina en español funciona bien entre 0.7 y 0.9
DISTANCE_THRESHOLD = 0.85

# creatividad del LLM — cerca de 0 para respuestas técnicas y consistentes
TEMPERATURE = 0.1

# largo máximo de la respuesta, aprox. 350-400 palabras en español
MAX_TOKENS = 512

# normalizar a norma 1 antes de indexar, requerido cuando se usa similitud coseno
NORMALIZE_EMBEDDINGS = True

# preguntas más largas que esto se rechazan sin consultar al LLM
INJECTION_MAX_LENGTH = 2000
