# Batch Cooking App

App web personal para organizar batch cooking semanal e inventario.

## Objetivo

1. Ir al súper con la lista de la compra ya hecha.
2. Organizar la semana asignando comidas a días el sábado.
3. Tener tracking de los alimentos y optimizar el tiempo.

Solo para mí. Web responsive (uso móvil en el súper).

## Stack

- **FastAPI** (backend + routing)
- **Jinja2** (templates) + **HTMX** (interacciones sin reload)
- **SQLAlchemy async** (ORM) · **Pydantic** (schemas) · **Alembic** (migraciones)
- **PostgreSQL** (en docker-compose)
- **uv** (gestión de dependencias)

## Estructura del repo

```
batch-cooking-app/
├── pyproject.toml          (uv)
├── docker-compose.yml      (postgres)
├── alembic.ini · alembic/  (migraciones)
├── .env.example
├── src/batch_cooking/
│   ├── main.py · config.py · database.py
│   ├── core/                    base classes y excepciones
│   ├── models/                  SQLAlchemy ORM
│   ├── repositories/            acceso a BD (sin lógica de negocio)
│   │   └── base.py              BaseRepository
│   ├── services/                lógica de negocio
│   │   ├── base.py              BaseService
│   │   └── dependencies/        get_X_from_session + FastAPI Depends
│   ├── routers/                 una carpeta por página: router.py + schemas.py
│   │   ├── home/ · week/ · shopping_list/
│   │   └── planner/ · cooking/ · inventory/ · recipes/
│   └── templates/               Jinja2 (+ partials/ para fragmentos HTMX)
├── static/                      css y js
└── tests/
```

### Reglas de arquitectura

- `router → service → repository`.
- Cada router tiene **sus propios schemas** (input/output).
- Services usan los schemas de los routers (la API es la única vía de entrada).
- Repositories: **solo acceso a BD**, sin lógica de negocio.
- Dependencias **entre services**, nunca entre repositories.
- En `services/dependencies/X.py`: una `get_X_from_session(db)` + una FastAPI dep que la llama.

## Páginas

### 1. `/home` (hub)
- Botones a todas las páginas.
- Listado de **alimentos caducados** (y solo eso).

### 2. Semana
- Calendario con los días de la semana.
- **Huecos por día configurables** (no fijo a comida + cena: el usuario define en settings sus huecos por defecto, ej: `["comida", "cena"]`).
- Acciones por hueco: ✓ comido / → no comido.

### 3. Lista de la compra
- Checklist persistente (no se borra entre semanas).
- Items agrupados por categoría.
- Permite añadir items manualmente cualquier día.
- Recibe ingredientes desde Planificar.
- Los items volcados desde Planificar muestran de qué planificación vienen (etiqueta visible).
- Al marcar comprado → mueve al Inventario alimentos.

### 4. Planificar
- Elegir recetas de la biblioteca.
- Asignarlas a los huecos de la semana.
- Confirmar → vuelca ingredientes a Lista de la compra (etiquetados con plan de origen).

### 5. Cocinar
- Lista de las recetas planificadas
- Confirmas raciones reales obtenidas y dónde van (nevera / congelador).
- Resta ingredientes del Inventario alimentos.
- Suma raciones al Inventario platos (con caducidad calculada).

### 6. Inventario
- Pestaña **Alimentos**: ingredientes + items sueltos. Editar / eliminar.
- Pestaña **Platos**: raciones cocinadas, ordenadas por caducidad.

### 7. Recetas
- Biblioteca CRUD con tags planos.
- Campos: nombre, ingredientes con cantidades, raciones que produce, días nevera, días congelador, tags.

## Modelo de datos

| Tabla | Campos clave |
|---|---|
| `ingredient` | id · name · default_unit · category |
| `recipe` | id · name · servings_produced · days_fridge · days_freezer · notes |
| `recipe_ingredient` | recipe_id · ingredient_id · quantity · unit |
| `tag` | id · name |
| `recipe_tag` | recipe_id · tag_id |
| `plan` | id · week_start · created_at · status (draft/confirmed/cooked) |
| `meal_slot` | id · plan_id · date · slot_label · recipe_id (nullable) · status (empty/planned/eaten/skipped) |
| `shopping_list_item` | id · name · ingredient_id (nullable) · quantity · unit · category · source_plan_id (nullable) · is_purchased · added_at |
| `food_inventory` | id · name · ingredient_id (nullable) · quantity · unit · category · expiry_date (nullable) · added_at |
| `dish_inventory` | id · recipe_id · recipe_name_snapshot · servings_remaining · location (fridge/freezer) · cooked_at · expiry_date |
| `settings` | clave/valor: `default_meal_slots` (lista), etc. |

### Notas del modelo

- **`meal_slot.recipe_id`** (no apunta a un `dish_inventory_id`): el inventario de platos es **uno general**. Al marcar "comido" se resta 1 ración del stock disponible de esa receta (FIFO por caducidad).
- **`meal_slot.slot_label`** es texto libre ("comida", "cena", "merienda"…). Settings guarda los slots por defecto pero se pueden añadir/quitar por plan.
- **`recipe_name_snapshot`** en dish_inventory: si renombras o borras una receta, los platos cocinados conservan su nombre.
- **Sin histórico de comidas en v1**: al consumir/desechar, se decrementa o borra. Se puede añadir log después.

## Reglas de negocio

- Lista de la compra es **persistente**: acumula items manuales + ingredientes de Planificar.
- **Dos inventarios**: Alimentos (g/unidades) ←gasta al cocinar→ Platos (raciones) ←gasta al comer.
- Caducidad de Platos calculada desde la receta (nevera vs congelador).
- Lo no comido un día → pool **Disponible** dentro de Semana.

## Frecuencia de uso

- Diario: Semana, Lista.
- Sábado: Planificar → Cocinar.
- Ocasional: Recetas, Inventario.

## Parkeado para v2

- Optimizador de orden de cocción (horno → cocciones → sartén → frío).
- Histórico de comidas.
