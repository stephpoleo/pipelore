# 🔮 Pipelore

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-En%20Desarrollo-yellow)

**Convierte la documentación de tu equipo en un asistente inteligente.**

Pipelore es un chatbot potenciado por RAG (Retrieval-Augmented Generation) que transforma la documentación estática en `.md` en un asistente conversacional con IA. Pregunta sobre tus pipelines de datos, arquitectura, reglas de negocio y procesos — y obtén respuestas instantáneas y precisas basadas en tu propia documentación.

No más buscar en wikis. No más preguntar "¿quién hizo este pipeline?". Solo pregúntale a Pipelore.

---

## 📚 Tabla de Contenido

1. [Problema](#-problema)
2. [Solución](#-solución)
3. [Características](#-características)
4. [Arquitectura](#-arquitectura)
5. [Flujo Lógico de Datos](#-flujo-lógico-de-datos)
6. [Decisiones de Diseño](#-decisiones-de-diseño)
7. [Stack Tecnológico](#-stack-tecnológico)
8. [Formato recomendado para los `.md`](#-formato-recomendado-para-los-md)
9. [Requisitos](#-requisitos)
10. [Instalación](#-instalación)
11. [Ejemplos de uso](#-ejemplos-de-uso)
12. [Estructura del proyecto](#-estructura-del-proyecto)
13. [Seguridad y Privacidad](#-seguridad-y-privacidad)
14. [Métricas de evaluación](#-métricas-de-evaluación)
15. [Roadmap](#-roadmap)

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

## 🔄 Flujo Lógico de Datos

El pipeline transforma documentos `.md` en respuestas fundamentadas siguiendo 7 etapas secuenciales:

```
📄 Archivos .md
      │
      ▼
┌─────────────┐
│  1. INGESTA │  loader.py — Lee archivos del disco
└──────┬──────┘
       │  List[str] (texto crudo)
       ▼
┌─────────────┐
│  2. PARSEO  │  LangChain Document — Estructura el texto con metadata
└──────┬──────┘
       │  List[Document] con filename como metadata
       ▼
┌──────────────┐
│  3. CHUNKING │  MarkdownHeaderTextSplitter — Fragmenta por secciones
└──────┬───────┘
       │  List[Document] con header + filename como metadata
       ▼
┌──────────────────┐
│  4. EMBEDDINGS   │  Jina v2-base-es — Vectoriza cada chunk
└──────┬───────────┘
       │  List[float[768]] por chunk
       ▼
┌──────────────────┐
│  5. INDEXACIÓN   │  ChromaDB — Almacena vectores + texto + metadata
└──────────────────┘
       │
       │  (en tiempo de consulta)
       ▼
┌──────────────────┐
│  6. RETRIEVAL    │  Top-K chunks por similitud coseno
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  7. GENERACIÓN   │  LLaMA 3.1 8B — Respuesta con citas de fuentes
└──────────────────┘
```

### Detalle de cada etapa

| # | Etapa | Herramienta | Input | Output | Decisión técnica |
|---|---|---|---|---|---|
| 1 | **Ingesta** | Python `pathlib` | Directorio `docs/` | Texto crudo + nombre de archivo | Lectura recursiva para soportar subcarpetas por equipo |
| 2 | **Chunking** | `MarkdownHeaderTextSplitter` | Texto crudo | Chunks con `{filename, section_header}` en metadata | Fragmentar por headers (`#`, `##`) respeta los límites semánticos del documento |
| 4 | **Embeddings** | `jina-embeddings-v2-base-es` | Texto de cada chunk | Vector de 768 dimensiones | Modelo bilingüe español/inglés, 100% local, optimizado para recuperación de información |
| 5 | **Indexación** | ChromaDB | Vector + texto + metadata | Colección persistente en disco | Base vectorial local, sin dependencias de nube, soporte nativo para metadata |
| 6 | **Retrieval** | ChromaDB `.query()` | Vector de la pregunta | Top-K chunks más similares | Similitud coseno sobre vectores Jina — misma familia de embeddings garantiza comparabilidad |
| 7 | **Generación** | LLaMA 3.1 8B via Ollama | Chunks + pregunta | Respuesta en lenguaje natural con citas | Modelo open-source, sin API keys, responde en español |

---

## 🧠 Decisiones de Diseño

### ¿Por qué ChromaDB y no pgvector o FAISS?

ChromaDB fue elegida por tres razones concretas:
1. **Persistencia zero-config**: guarda los vectores en disco con una línea de código, sin servidor ni migraciones
2. **Metadata nativa**: soporta filtros por `filename` o `section_header` directamente en la query, lo que habilita las citas de fuentes
3. **Ideal para la escala del proyecto**: una empresa mediana con ~500 documentos `.md` no necesita la complejidad de pgvector; ChromaDB es suficiente y significativamente más simple de operar

### ¿Por qué Jina Embeddings v2-base-es?

- Es el único modelo open-source optimizado específicamente para **español técnico**
- Soporta ventanas de contexto de 8192 tokens (crítico para secciones de documentación largas)
- Corre en CPU o GPU sin configuración adicional (vía HuggingFace `transformers`)
- La alternativa (OpenAI `text-embedding-3-small`) requiere API key y envía datos a servidores externos — incompatible con el requisito de privacidad

### ¿Por qué fragmentar por headers Markdown y no por tamaño fijo?

El **chunking convencional** corta por tamaño fijo de caracteres. El resultado es texto partido en medio de una idea:

```
Chunk 1: "...calcula bonos para México y Brasil. Este dom"
Chunk 2: "inio alimenta los dashboards de BI que el equipo..."
```

El Chunk 2 empieza con "inio" — sin contexto, sin saber de qué trata. El embedding que genera ese fragmento es ruido, y el retrieval va a fallar o traer resultados irrelevantes.

**Lo que hace Pipelore** es usar la estructura del documento como unidad de corte. Cada `##` define una sección semántica completa, y el splitter la trata como un chunk independiente:

```
Chunk recuperado:
  page_content: "## Reglas de Negocio\n\n| Bono | Regla |\n|------|-------|\n| BONO_LUUNA | $400 para órdenes 40k-100k..."
  metadata: {
    "Header 1": "Bonos Retail (México y Brasil)",
    "Header 2": "Reglas de Negocio",
    "filename": "bonos.md"
  }
```

Ese chunk sabe tres cosas sobre sí mismo antes de que alguien lo lea: a qué dominio pertenece (`Header 1`), de qué trata (`Header 2`) y de qué archivo vino (`filename`).

**La diferencia real en el RAG:** cuando alguien pregunta "¿cuáles son los bonos individuales por orden en México?", el modelo de embeddings compara ese vector contra todos los chunks. El chunk de `## Reglas de Negocio` de `bonos.md` gana porque su `page_content` contiene exactamente esa tabla. Con chunking convencional, la mitad de la tabla estaría en un chunk y la otra mitad en el siguiente — el LLM armaría una respuesta incompleta.

Los metadatos `Header 1` y `Header 2` tampoco son decorativos: en producción se usan para construir la cita de fuente ("según la sección Reglas de Negocio del documento Bonos Retail") y para filtrar la búsqueda si el usuario especifica de qué dominio quiere la respuesta.

### ¿Por qué LLaMA 3.1 8B y no un modelo más grande?

- Corre en hardware accesible (8GB VRAM) con latencia aceptable (<10s por respuesta)
- Para RAG, el LLM es un **sintetizador**, no una fuente de conocimiento — el contexto recuperado hace el trabajo pesado; el tamaño del modelo importa menos que en generación libre
- El modelo más grande (70B) requiere hardware de ~40GB VRAM, incompatible con el requisito de deployment local en laptops de equipo

### ¿Por qué Ollama y no llama.cpp o HuggingFace transformers directamente?

Ollama es la capa de infraestructura que hace que correr LLMs localmente sea operacionalmente simple:
- **Un instalador** — sin compilar código, sin configurar CUDA manualmente
- **Gestión de modelos** — descarga, versioning y switching de modelos con un comando (`ollama pull`)
- **API REST local** — expone `localhost:11434`, el cliente Python solo hace HTTP requests; el servidor maneja GPU/CPU automáticamente
- **llama.cpp** requiere compilar desde source y configurar bindings manualmente
- **HuggingFace `transformers`** para inferencia carga el modelo completo en memoria Python, lo que es significativamente más pesado que Ollama que lo maneja como proceso separado optimizado

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Propósito |
|---|---|---|
| Frontend | Streamlit | Interfaz de chat conversacional |
| Backend | Python + FastAPI | API REST para el RAG |
| Base Vectorial | ChromaDB | Almacenamiento y búsqueda de embeddings |
| Embeddings | jinaai/jina-embeddings-v2-base-es | Modelo bilingüe español/inglés (local) |
| LLM generación | LLaMA 3.1 8B via Ollama | Generación de respuestas (local) |
| LLM seguridad | llama-guard3:8b via Ollama | Clasificación de seguridad de inputs (local) |
| Chunking | LangChain Text Splitters | Fragmentación de documentos |

---

## 🧰 Formato recomendado para los `.md`

Para mejores resultados en el RAG, cada documento debe seguir esta estructura. Los headers son la unidad mínima de chunking — una sección mal nombrada o ausente significa que esa información **no será recuperada** cuando sea relevante.

### Template

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

### Qué pregunta responde cada sección en el RAG

| Sección | Pregunta que habilita | Obligatoria |
|---|---|---|
| `# Nombre del Proyecto` | "¿Qué proyectos existen?" | ✅ Sí |
| `## Descripción General` | "¿Qué hace X?" / "¿Para qué sirve X?" | ✅ Sí |
| `## Owner` | "¿Quién hizo X?" / "¿A quién le pregunto sobre X?" | ✅ Sí |
| `## Arquitectura` | "¿Cómo fluyen los datos en X?" | ✅ Sí |
| `## Fuentes de Datos` | "¿De dónde vienen los datos de X?" | ✅ Sí |
| `## Transformaciones` | "¿Qué transformaciones hace X?" | ✅ Sí |
| `## Reglas de Negocio` | "¿Cómo se calcula [KPI] en X?" | ✅ Sí |
| `## Frecuencia de Ejecución` | "¿Cuándo corre X?" / "¿Es real-time o batch?" | ⚡ Recomendada |
| `## Dependencias` | "¿Qué se rompe si cambio la tabla Y?" | ⚡ Recomendada |
| `## Output / Entregables` | "¿Qué produce X?" / "¿Dónde veo el resultado?" | ⚡ Recomendada |
| `## Contacto` | "¿A quién llamo si X falla?" | 🔵 Opcional |

### Reglas de consistencia

> Estas reglas aseguran que el sistema encuentre la información correctamente.

1. **Usa exactamente estos nombres de headers** — no uses variantes como `## Descripción` o `## Dueño`; el splitter los trata como secciones diferentes
2. **Un proyecto por archivo** — no combines múltiples proyectos en un solo `.md`
3. **Texto en las secciones, no solo código** — el RAG recupera texto; los bloques de SQL sin contexto no responden preguntas en lenguaje natural
4. **Evita tablas anidadas en secciones críticas** — los campos de tablas Markdown se pierden en el chunking; prefiere listas con `-`

### Ejemplo completo

```markdown
# Proyecto Bonos Retail

## Descripción General
Calcula los incentivos mensuales del equipo retail de la empresa.
Consume datos de ventas por categoría y aplica los porcentajes de comisión
definidos por el área de Recursos Humanos. El output es un reporte Excel
que RR.HH. usa para procesar nómina.

## Owner
Stephanie Morales — equipo Data Engineering.
Construido en Q3 2024, mantenimiento activo.

## Arquitectura
Snowflake (tabla `ventas_retail`) → Python (cálculo de bonos) → Excel → SharePoint.
El script corre en Airflow, DAG `dag_bonos_retail`.

## Fuentes de Datos
- Tabla `dw.ventas_retail` en Snowflake
- Tabla `rrhh.empleados` en Snowflake (para el mapeo vendedor → sucursal)

## Transformaciones
1. Filtra ventas del mes anterior (columna `fecha_venta`)
2. Agrupa por `id_vendedor` y `categoria_producto`
3. Aplica porcentaje de comisión según categoría
4. Une con tabla de empleados para agregar nombre y sucursal

## Reglas de Negocio
- Categoría "Producto A": 3% sobre ventas brutas
- Categoría "Sofás": 5% sobre ventas brutas
- Categoría "Puffs": 2% sobre ventas brutas
- Umbral mínimo: el bono no se paga si las ventas del mes < $50,000
- Los devoluciones se descuentan de las ventas brutas antes del cálculo

## Frecuencia de Ejecución
El día 15 de cada mes a las 08:00 AM (cron: `0 8 15 * *`).
Trigger manual disponible en Airflow si RR.HH. necesita recalcular.

## Dependencias
- `dw.ventas_retail` es alimentada por el proyecto `etl_frappe_ventas`
- Si cambia el esquema de `rrhh.empleados`, este proyecto se rompe
- El dashboard de `comisiones_gerencia` consume el Excel de output

## Output / Entregables
Archivo Excel `bonos_YYYY_MM.xlsx` subido a SharePoint en:
`/equipos/data/reportes_mensuales/bonos/`

## Contacto
Stephanie Morales (slack: @stephanie) para lógica de negocio.
Ana García de RR.HH. (slack: @ana.garcia) para validar porcentajes.
```

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

Ollama es la aplicación que corre el LLM localmente. Son dos pasos separados:

**a) Instalar Ollama** (aplicación del sistema, no una librería Python):
Descarga e instala el ejecutable desde https://ollama.com/download. Una vez instalado, queda corriendo como servicio en background en `localhost:11434`.

**b) Descargar los modelos** (~5GB cada uno, solo la primera vez):
```bash
ollama pull llama3.1:8b       # LLM de generación de respuestas
ollama pull llama-guard3:8b   # clasificador de seguridad de inputs
```

**c) Verificar que están corriendo:**
```bash
ollama list   # debe mostrar llama3.1:8b y llama-guard3:8b en la lista
```

> **Nota:** `pip install ollama` instala el cliente Python que se comunica con el servidor, pero no instala el servidor ni los modelos. Ambos son necesarios.

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
├── notebooks/
│   ├── etl_exploration.ipynb    # Pipeline ETL + RAG + Safety (construcción)
│   └── evaluation.ipynb         # Benchmark de calidad y latencia (evaluación)
├── evaluations/
│   └── eval_log.json            # Registro acumulativo de corridas de evaluación
├── docs/
│   └── ejemplo_proyecto.md      # Documento de ejemplo para pruebas
├── tests/
│   ├── test_queries.py          # Queries de prueba
│   └── test_evaluation.py       # Evaluación automatizada
└── README.md
```

---

## 🔒 Seguridad y Privacidad

**Ningún dato sale de tu máquina.** Todos los modelos corren localmente con Ollama, sin llamadas a APIs externas.

### Filtro de seguridad de inputs — 3 capas en orden

Cada pregunta pasa por tres checks antes de llegar al pipeline RAG:

```
pregunta
  │
  ├─ Check 1: longitud > 2000 chars  →  UNSAFE  razón: prompt_too_long
  ├─ Check 2: regex (injection + código destructivo)  →  UNSAFE  razón: injection_pattern
  └─ Check 3: llama-guard3:8b (contenido dañino)  →  UNSAFE  razón: content_policy
                                                    →  SAFE → RAG → respuesta
```

**Por qué 3 capas y no solo una:**

| Capa | Qué detecta | Por qué no alcanza con solo LLM |
|---|---|---|
| Longitud | Inputs de >2000 chars | El LLM no debería gastarse en clasificar spam masivo |
| Regex | Prompt injection (`olvida tus instrucciones`), código destructivo (`script que elimine registros`) | Son ataques **estructurales** — llama-guard3 no los cubre (no existe categoría S1-S14 para injection) |
| llama-guard3 | Contenido dañino semántico: sexual, odio, violencia, armas, etc. | Un LLM de propósito general (LLaMA 3.1) falla porque el sesgo RLHF lo hace "demasiado útil" para clasificar |

**¿Por qué no usar LLaMA 3.1 para clasificar?** LLaMA 3.1 fue entrenado con RLHF para ser útil — ese sesgo lo hace resistente a clasificar como UNSAFE incluso con few-shot examples explícitos. En pruebas, clasificó mal 5 de 7 casos UNSAFE. `llama-guard3` fue entrenado **específicamente** para clasificación de seguridad, no para ser un asistente.

### Tabla de protección

| Capa | Protección |
|---|---|
| Datos | Solo archivos `.md` — sin código, credenciales ni accesos |
| Modelos | 100% locales — Jina (HuggingFace) + LLaMA + llama-guard3 (Ollama) |
| Input | 3 checks: longitud + regex + llama-guard3 |
| Prompt | Contexto acotado — el LLM solo ve los chunks recuperados |
| Output | Respuesta fundamentada en contexto, no en conocimiento propio del modelo |

### Arquitectura de producción recomendada

Para un deployment empresarial, se recomienda:
- Modelos corriendo en AWS EC2 (g5.xlarge) dentro de la VPC de la empresa
- ChromaDB o pgvector en la misma red privada
- S3 privado con cifrado para los documentos fuente
- Sin dependencias de APIs externas (Gemini, OpenAI, etc.)

---

## 📊 Métricas de evaluación

El sistema incluye un benchmark automatizado con 15 preguntas escritas a mano (factuales, comparativas y preguntas sin respuesta). Los resultados se registran en `evaluations/eval_log.json` para comparar entre versiones.

### Métricas de calidad

| Métrica | Método | Qué mide |
|---|---|---|
| **Faithfulness** (Precision) | LLM-as-a-Judge | Claims correctos / Total claims generados. ¿Cuánto de lo que dice es verdad? |
| **Recall** | LLM-as-a-Judge | Info cubierta del ground truth / Total info esperada. ¿Cuánto de lo que debía decir, dijo? |
| **F1** | Calculada | Media armónica de precision y recall. Balance entre no alucinar y ser completo |
| **Correctness** | Similaridad coseno (Jina) | Similaridad semántica entre respuesta generada y esperada. Señal complementaria, no definitiva |
| **Context Relevancy** | LLM-as-a-Judge | Chunks relevantes / Total chunks recuperados. ¿El retrieval trae información útil? |
| **Accuracy** | Umbral F1 > 0.7 | % de preguntas que el sistema responde correctamente |

### Métricas de rendimiento

| Métrica | Etapa | Objetivo |
|---|---|---|
| Latencia de safety | `is_safe_v2()` (regex + llama-guard3) | < 2s |
| Latencia de retrieval | Embedding + búsqueda ChromaDB | < 200ms |
| Latencia de generación | LLaMA 3.1 8B via Ollama | < 60s |
| Latencia total | Pipeline completo | < 90s |

### Guía para interpretar resultados

Después de ejecutar la evaluación (celda 8b.5 del notebook), el sistema genera una tabla con scores por pregunta y un resumen. Usa esta guía para interpretar:

**Faithfulness (la métrica más importante):**
- `> 0.8` — Excelente: el RAG responde con información del contexto
- `0.5 – 0.8` — Aceptable: hay algunos claims no soportados, revisar cuáles
- `< 0.5` — Problema: el RAG está alucinando. Revisar el detalle de claims en `faith_detail`

**Recall:**
- `> 0.7` — Las respuestas son completas
- `< 0.5` — El RAG omite información importante. Posibles causas: TOP_K muy bajo, chunks relevantes no recuperados

**Context Relevancy:**
- `> 0.7` — El retrieval trae chunks útiles
- `< 0.5` — Mucho ruido. Bajar DISTANCE_THRESHOLD o ajustar TOP_K

**Correctness (similaridad semántica):**
- Útil como señal secundaria pero **no confiar como detector de alucinaciones**: frases contradictorias pueden tener alta similaridad semántica (ej: "se ejecuta diario" vs "se ejecuta mensual" → coseno alto)

**Preguntas sin respuesta en los docs:**
- Si el RAG responde "no tengo información" → faithfulness debería ser alta (el claim "no tengo info" está soportado por la ausencia en el contexto)
- Si el RAG inventa una respuesta → faithfulness baja, lo cual es correcto — indica alucinación

**Comparación entre versiones:**
- Cada corrida se guarda en `evaluations/eval_log.json` con la configuración completa (modelo, temperatura, TOP_K, prompts)
- Al ejecutar una segunda corrida, el notebook muestra el delta de cada métrica vs la corrida anterior
- Usar el campo `notes` para documentar qué se cambió y por qué

**Playbook de mejora cuando se detectan alucinaciones:**

| Nivel | Acción | Cuándo |
|---|---|---|
| 1 | Ajustar prompt del sistema | Faithfulness < 0.8 en preguntas con contexto claro |
| 2 | Ajustar retrieval (TOP_K, DISTANCE_THRESHOLD) | Context relevancy < 0.5 |
| 3 | Cambiar modelo (LLaMA 3.3 8B, Qwen 2.5 7B) | Métricas no mejoran con ajustes 1 y 2 |
| 4 | Técnicas avanzadas (re-ranking, chain-of-thought) | Solo si 1-3 no son suficientes |

---

## 🗺️ Roadmap

### Fase 1 — Diseño y Planificación ✅ (Entregable actual)
> **Hito:** Diseño lógico completo del sistema, selección de herramientas y arquitectura documentada.

- [x] Diseño del flujo lógico de datos (Ingesta → Indexación)
- [x] Selección y justificación del stack tecnológico (ChromaDB, Jina, LLaMA)
- [x] Definición del formato de documentación `.md` y estrategia de chunking
- [x] Roadmap técnico con fases, hitos y entregables
- [x] Notebook exploración ETL (`notebooks/01_etl_exploration.ipynb`)

**Entregables:** README con arquitectura + flujo lógico, notebook guiado, doc de ejemplo.

---

### Fase 2 — ETL Funcional e Indexación 🚧 (Próxima)
> **Hito:** Pipeline ETL ejecutable de punta a punta: desde `.md` hasta consulta semántica.

- [ ] Implementar `etl/loader.py` — ingesta de archivos `.md` desde disco
- [ ] Implementar `etl/chunker.py` — fragmentación con `MarkdownHeaderTextSplitter`
- [ ] Implementar `etl/indexer.py` — indexación en ChromaDB con metadata
- [ ] Implementar `rag/embeddings.py` — modelo Jina v2-base-es vía HuggingFace
- [ ] Implementar `rag/retriever.py` — búsqueda semántica top-K en ChromaDB
- [ ] Script de re-indexación automática al detectar cambios en `.md`
- [ ] Tests de integración del pipeline ETL

**Entregables:** ETL funcional documentado, colección ChromaDB con ≥5 proyectos indexados, demo de retrieval con queries de prueba.

---

### Fase 3 — RAG Completo, Frontend y Evaluación 📋 (Planificada)
> **Hito:** Sistema RAG conversacional listo para uso por el equipo.

- [ ] Implementar `rag/generator.py` — integración con LLaMA via Ollama
- [ ] Implementar `rag/pipeline.py` — pipeline RAG completo con citas de fuentes
- [x] Implementar `pipelore/safety.py` — 3 capas: longitud + regex + llama-guard3 (8/8 test cases ✅)
- [ ] Frontend Streamlit con chat, sidebar de proyectos y citas de fuentes
- [ ] Backend FastAPI con endpoint `/query`
- [x] Sistema de evaluación LLM-as-a-Judge — faithfulness, recall, F1, context relevancy (notebook sección 8b)
- [x] Métricas de latencia por etapa — safety, retrieval, generación (notebook sección 8a)
- [x] Benchmark con 15 preguntas y registro de versiones en `evaluations/eval_log.json`
- [ ] Diccionario de datos (integración con metadata de Snowflake)
- [ ] Deployment en AWS (EC2 + VPC) con documentación

**Entregables:** Sistema RAG en producción, reporte de evaluación con métricas de calidad, guía de deployment.

---

## 📄 Licencia

MIT

---

## 👩‍💻 Autora

Desarrollado como proyecto final del CERTI AI Data Engineer — BSG Institute 2025.

https://huggingface.co/sentence-transformers
https://huggingface.co/jinaai/jina-embeddings-v2-base-es
https://huggingface.co/spaces/mteb/leaderboard
https://reference.langchain.com/python/langchain-text-splitters
https://www.kaggle.com/code/ksmooi/langchain-mastering-text-splitting
https://medium.com/@wetrocloud/why-markdown-is-the-best-format-for-llms-aa0514a409a7
