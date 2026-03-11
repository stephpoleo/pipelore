# 🔮 Pipelore

**Convierte la documentación de tu equipo en un asistente inteligente.**

Pipelore es un chatbot potenciado por RAG (Retrieval-Augmented Generation) que transforma la documentación estática en `.md` en un asistente conversacional con IA. Pregunta sobre tus pipelines de datos, arquitectura, reglas de negocio y procesos — y obtén respuestas instantáneas y precisas basadas en tu propia documentación.

No más buscar en wikis. No más preguntar "¿quién hizo este pipeline?". Solo pregúntale a Pipelore.

---

## 🎯 Problema

En los equipos de ingeniería de datos, la documentación existe pero nadie la lee. Cuando necesitas entender o modificar un pipeline que construyó otra persona, pierdes horas leyendo archivos `.md` o buscando al autor original. Este problema se multiplica durante onboardings, transferencias de conocimiento y colaboración entre equipos.

## 💡 Solución

Pipelore ingesta la documentación `.md` de tu equipo, la fragmenta en chunks, genera embeddings semánticos y los almacena en una base de datos vectorial. Cuando un usuario hace una pregunta, el sistema recupera los fragmentos más relevantes y usa un LLM local para generar una respuesta precisa y fundamentada en el contexto — con citas de las fuentes.

**Todo corre localmente. Ningún dato sale de tu máquina.**

---

## ✨ Características

- 🤖 **Q&A en lenguaje natural** sobre documentación técnica
- 📄 **Markdown-first** — se alimenta directo de tus archivos `.md`
- 🔒 **100% local y privado** — sin llamadas a APIs externas
- 📎 **Citas de fuentes** — cada respuesta indica de qué documento proviene
- 🔍 **Búsqueda semántica** — encuentra información por significado, no solo por palabras clave
- ⚡ **Retrieval rápido** — búsqueda vectorial con ChromaDB
- 📊 **Evaluación integrada** — LLM-as-a-Judge para métricas de calidad

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│                    Streamlit                          │
│                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Chat    │  │  Sidebar de  │  │  Fuentes      │ │
│  │ Interface │  │  Proyectos   │  │  citadas      │ │
│  └──────────┘  └──────────────┘  └───────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (localhost)
                       ▼
┌─────────────────────────────────────────────────────┐
│                    BACKEND                           │
│                Python + FastAPI                      │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              RAG Pipeline                     │   │
│  │                                               │   │
│  │  1. Embedding de la pregunta (Jina)          │   │
│  │  2. Búsqueda en ChromaDB (similitud)         │   │
│  │  3. Armar prompt con contexto recuperado     │   │
│  │  4. Generar respuesta (LLaMA via Ollama)     │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌─────────┐ ┌──────────────────┐
   │  ChromaDB  │ │ Ollama  │ │ Jina Embeddings  │
   │ (vectores) │ │ LLaMA   │ │ v2-base-es       │
   │  local     │ │ 3.1 8B  │ │ (Hugging Face)   │
   └────────────┘ └─────────┘ └──────────────────┘
          ▲
          │ ETL
   ┌────────────┐
   │  📄 .md    │
   │  del equipo│
   └────────────┘
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Propósito |
|---|---|---|
| Frontend | Streamlit | Interfaz de chat conversacional |
| Backend | Python + FastAPI | API REST para el RAG |
| Base Vectorial | ChromaDB | Almacenamiento y búsqueda de embeddings |
| Embeddings | jinaai/jina-embeddings-v2-base-es | Modelo bilingüe español/inglés (local) |
| LLM | LLaMA 3.1 8B via Ollama | Generación de respuestas (local) |
| Chunking | LangChain Text Splitters | Fragmentación de documentos |

---

## 📋 Requisitos

### Hardware mínimo
- GPU con 8GB+ de VRAM (NVIDIA RTX recomendada)
- 16GB+ de RAM
- 10GB de espacio en disco

### Software
- Python 3.11+
- [Ollama](https://ollama.com) instalado
- CUDA (para aceleración GPU)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/pipelore.git
cd pipelore
```

### 2. Instalar Ollama y descargar LLaMA

```bash
# Instalar Ollama desde https://ollama.com
ollama pull llama3.1:8b
```

### 3. Instalar dependencias de Python

```bash
cd backend
pip install -r requirements.txt
```

### 4. Agregar tu documentación

Coloca tus archivos `.md` en la carpeta `backend/docs/`:

```
backend/docs/
├── proyecto_bonos.md
├── proyecto_warehouse.md
├── proyecto_comisiones.md
├── arquitectura_general.md
└── ...
```

### 5. Indexar documentos

```bash
python -m etl.indexer
```

### 6. Iniciar el backend

```bash
uvicorn main:app --reload --port 8000
```

### 7. Iniciar el frontend

```bash
cd frontend
streamlit run app.py
```

Abre `http://localhost:8501` y empieza a preguntar.

---

## 💬 Ejemplos de uso

```
👤 "¿Qué hace el proyecto de bonos?"
🔮 "El proyecto de bonos calcula los incentivos mensuales del equipo
    retail. Se basa en ventas de tres categorías: Producto A (3%),
    sofás (5%) y puffs (2%). Se ejecuta el día 15 de cada mes."
    📎 Fuente: proyecto_bonos.md

👤 "¿De dónde vienen los datos del dashboard de warehouse?"
🔮 "Los datos provienen del sistema Frappe, que envía webhooks
    a AWS API Gateway. De ahí se procesan y cargan en Snowflake..."
    📎 Fuente: proyecto_warehouse.md

👤 "¿Qué proyectos se afectan si cambio la tabla de productos?"
🔮 "La tabla de productos es utilizada por tres proyectos:
    bonos, comisiones y el scraper de Walmart..."
    📎 Fuentes: proyecto_bonos.md, proyecto_comisiones.md, proyecto_walmart.md
```

---

## 📁 Estructura del proyecto

```
pipelore/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Configuración global
│   ├── rag/
│   │   ├── embeddings.py        # Modelo Jina (Hugging Face)
│   │   ├── retriever.py         # Búsqueda en ChromaDB
│   │   ├── generator.py         # Llamadas a Ollama/LLaMA
│   │   ├── pipeline.py          # Pipeline RAG completo
│   │   └── security.py          # Sanitización input/output
│   ├── etl/
│   │   ├── loader.py            # Lectura de archivos .md
│   │   ├── chunker.py           # Fragmentación con LangChain
│   │   └── indexer.py           # Indexación en ChromaDB
│   ├── evaluation/
│   │   ├── metrics.py           # Latencia, throughput
│   │   └── judge.py             # LLM-as-a-Judge
│   ├── docs/                    # Documentación .md del equipo
│   │   ├── proyecto_bonos.md
│   │   ├── proyecto_warehouse.md
│   │   ├── proyecto_walmart.md
│   │   ├── proyecto_comisiones.md
│   │   ├── arquitectura_general.md
│   │   └── onboarding_guia.md
│   └── requirements.txt
├── frontend/
│   └── app.py                   # Streamlit app
├── tests/
│   ├── test_queries.py          # Queries de prueba
│   └── test_evaluation.py       # Evaluación automatizada
└── README.md
```

---

## 🔒 Seguridad y Privacidad

| Capa | Protección |
|---|---|
| Datos | Solo archivos `.md` — sin código, credenciales ni accesos |
| Modelos | 100% locales — Jina (HuggingFace) + LLaMA (Ollama) |
| Input | Sanitización contra prompt injection |
| Prompt | System prompt con delimitadores estructurales |
| Output | Validación de respuestas antes de mostrar al usuario |

**Ningún dato sale de tu máquina.** Los modelos corren localmente en tu GPU, sin llamadas a APIs externas.

### Arquitectura de producción recomendada

Para un deployment empresarial, se recomienda:
- Modelos corriendo en AWS EC2 (g5.xlarge) dentro de la VPC de la empresa
- ChromaDB o pgvector en la misma red privada
- S3 privado con cifrado para los documentos fuente
- Sin dependencias de APIs externas (Gemini, OpenAI, etc.)

---

## 📊 Métricas de evaluación

### Rendimiento
| Métrica | Objetivo |
|---|---|
| Latencia de embedding | < 100ms |
| Latencia de retrieval | < 50ms |
| Latencia de generación | < 10s |
| Latencia total | < 15s |

### Calidad
| Métrica | Método |
|---|---|
| Relevancia | Cosine similarity + revisión manual |
| Fidelidad | LLM-as-a-Judge |
| Alucinaciones | LLM-as-a-Judge + revisión manual |

---

## 🗺️ Roadmap

- [x] Pipeline ETL (ingesta, chunking, embeddings)
- [x] RAG funcional con ChromaDB + LLaMA
- [x] Frontend con Streamlit
- [x] Métricas de evaluación
- [ ] Re-indexación automática al detectar cambios en `.md`
- [ ] Diccionario de datos (integración con metadata de Snowflake)
- [ ] Deployment en AWS (EC2 + VPC)
- [ ] Autenticación por roles
- [ ] Soporte multi-equipo con filtros

---

## 🧰 Formato recomendado para los `.md`

Para mejores resultados, documenta tus proyectos con esta estructura:

```markdown
# Nombre del Proyecto

## Descripción General
Qué hace, para quién, por qué existe.

## Owner
Quién lo construyó y mantiene.

## Arquitectura
De dónde vienen los datos, por dónde pasan, a dónde llegan.

## Fuentes de Datos
Qué tablas o sistemas alimentan este proyecto.

## Transformaciones
Qué se le hace a los datos (lógica, no SQL).

## Reglas de Negocio
Cómo se calculan los KPIs, fórmulas, condiciones.

## Frecuencia de Ejecución
Cada cuánto corre, trigger manual o automático.

## Dependencias
Qué otros proyectos o tablas dependen de este.

## Output / Entregables
Qué produce: dashboard, tabla, reporte, API.

## Contacto
A quién preguntar si algo falla.
```

---

## 📄 Licencia

MIT

---

## 👩‍💻 Autora

Desarrollado como proyecto final del CERTI AI Data Engineer — BSG Institute 2025.
