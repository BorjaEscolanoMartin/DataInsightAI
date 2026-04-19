# DataInsight AI

Plataforma web que convierte un CSV en visualizaciones interactivas, insights en lenguaje natural y predicciones automáticas mediante IA y ML, sin escribir una línea de código.

## Funcionalidades

- **Perfilado automático** — tipos de columnas, nulos, outliers, estadísticos descriptivos, cardinalidad
- **Visualizaciones interactivas** — histogramas, bar charts, series temporales, heatmap de correlaciones, scatter plots; generados automáticamente según el tipo de datos
- **Insights con LLM** — tendencias, anomalías, correlaciones y recomendaciones generados por Claude (Anthropic), clasificados y colapsables
- **Predicciones automáticas** — forecasting con Holt-Winters (statsmodels) si se detecta serie temporal; regresión baseline con RandomForest + feature importance si no
- **Informe PDF** — descarga con resumen del dataset, insights, métricas de predicción

## Arranque rápido

### Requisitos

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2

### Con Docker (recomendado)

```bash
# 1. Clona el repo
git clone <repo-url>
cd DataInsightAI

# 2. Crea los .env con tus claves
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
# Edita ambos archivos con tus credenciales de Supabase y Anthropic

# 3. Levanta todo
docker compose up --build

# Servicios disponibles:
#   web  → http://localhost:3000
#   api  → http://localhost:8000/docs
```

### Variables de entorno

**`apps/api/.env`**
| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | API key de [console.anthropic.com](https://console.anthropic.com) |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (Settings → API) |
| `SUPABASE_JWT_SECRET` | JWT secret (Settings → API) |
| `DATABASE_URL` | Conexión PostgreSQL (usar Supabase en prod) |
| `REDIS_URL` | Conexión Redis |

**`apps/web/.env.local`**
| Variable | Descripción |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL del proyecto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon/public key (Settings → API) |
| `NEXT_PUBLIC_API_URL` | URL de la API (`http://localhost:8000` en local) |

### Ejecutar los tests

```bash
docker compose run --rm api pytest tests/ -v
```

## Arquitectura

```
DataInsightAI/
├── apps/
│   ├── api/                  # FastAPI — procesamiento, ML, LLM
│   │   ├── app/
│   │   │   ├── routers/      # projects, datasets, analyses
│   │   │   ├── services/     # profiling, insights_llm, forecasting, ml_baseline, report
│   │   │   ├── workers/      # Celery tasks
│   │   │   ├── schemas/      # Pydantic v2
│   │   │   └── db/           # SQLAlchemy 2 + Alembic
│   │   └── tests/
│   └── web/                  # Next.js 15 (App Router)
│       └── src/
│           ├── app/          # Páginas (auth + dashboard)
│           ├── components/   # charts, insights, predictions, upload
│           └── lib/          # queries (TanStack Query), api client
├── docker-compose.yml
└── railway.json              # Configuración de deploy en Railway
```

### Flujo de análisis

```
CSV subido → Supabase Storage
    ↓
Celery worker
    ├── profile_csv()       — pandas: tipos, stats, outliers, chart specs
    ├── generate_insights() — Claude Sonnet (Anthropic SDK)
    └── run_forecast()      — statsmodels Holt-Winters
        o run_regression()  — scikit-learn RandomForest
    ↓
Analysis guardado en PostgreSQL (status: completed)
    ↓
Frontend polling → renderiza ChartGrid + InsightsPanel + PredictionsPanel
```

## Stack técnico

| Capa | Tecnología | Por qué |
|---|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS v4 | App Router + RSC, tipado estricto, utilidades CSS sin configuración |
| Componentes | shadcn/ui, Recharts | Accesibles, composables, sin opiniones sobre el diseño |
| Estado / fetch | TanStack Query | Cache, polling y mutaciones con muy poco boilerplate |
| Backend | Python 3.12, FastAPI, Pydantic v2 | Ecosistema de datos/ML, validación automática, OpenAPI gratis |
| LLM | Anthropic Claude Sonnet | Salida JSON estructurada fiable, prompt engineering sencillo |
| Forecasting | statsmodels (Holt-Winters) | Sin dependencias de compilación (vs Prophet/cmdstan), build rápido |
| ML baseline | scikit-learn RandomForest | Interpretable, robusto con pocos datos, feature importance directo |
| PDF | ReportLab | Sin dependencias de sistema (vs WeasyPrint/GTK), puro Python |
| Auth | Supabase Auth (ES256 JWT) | Gestión de usuarios lista para producción, gratis en el plan free |
| Base de datos | PostgreSQL 16 + SQLAlchemy 2 + Alembic | Migraciones versionadas, ORM tipado |
| Cola | Celery + Redis | Análisis pesados en background sin bloquear la API |
| Infra local | Docker Compose | Un comando levanta los 5 servicios |

## Deploy

### Backend → Railway

1. Conecta el repo en [railway.app](https://railway.app)
2. Configura las variables de entorno del backend
3. Añade un servicio Redis (plugin de Railway) y PostgreSQL o usa Supabase
4. Para el worker de Celery, crea un segundo servicio con el mismo repo y como start command: `celery -A app.workers.celery_app worker --loglevel=info --concurrency=2`

### Frontend → Vercel

1. Conecta el repo en [vercel.com](https://vercel.com)
2. Configura **Root Directory** → `apps/web`
3. Añade las variables de entorno del frontend
4. Deploy automático en cada push a `main`

## Fases de desarrollo

- [x] **Fase 0** — Scaffolding: monorepo, Docker Compose, hola mundo
- [x] **Fase 1** — Auth y proyectos: Supabase Auth, CRUD de proyectos
- [x] **Fase 2** — Subida y perfilado de CSV
- [x] **Fase 3** — Visualizaciones automáticas con Recharts
- [x] **Fase 4** — Análisis asíncrono con Celery
- [x] **Fase 5** — Insights en lenguaje natural con Claude
- [x] **Fase 6** — Predicciones (forecasting + regresión baseline)
- [x] **Fase 7** — Informe PDF descargable
- [x] **Fase 8** — Tests, configuración de deploy, documentación
