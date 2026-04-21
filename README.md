# Chinook Fullstack — Parcial 1 & 2

**Universidad Sergio Arboleda | Big Data e Ingeniería de Datos**
**Profesor:** Oscar Andrés Arias M.
**Estudiante:** Julian Esteban Rincón Rodríguez

---

## Descripción General

Este repositorio contiene la entrega completa de los dos parciales de la asignatura
**Big Data e Ingeniería de Datos**. El proyecto implementa un sistema end-to-end
que va desde una aplicación web transaccional hasta un Data Warehouse analítico
desplegado sobre AWS, pasando por pipelines ETL automatizados y reportes de
Business Intelligence.

---

## Parcial 1 — Aplicación Web Fullstack en AWS

### Objetivo

Diseñar e implementar una aplicación web fullstack desplegada en AWS que permita
gestionar y realizar compras de canciones sobre la base de datos **Chinook**,
incorporando buenas prácticas de arquitectura cloud, pruebas automatizadas y
un pipeline CI/CD completo.

### Arquitectura

```
Usuario
  └── EC2 Frontend (Nginx + React)
        └── /api/* → EC2 Backend (FastAPI + uvicorn)
                        └── Amazon RDS PostgreSQL (Chinook, privado)
```

### Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + Vite |
| Backend | FastAPI + Python 3.12 + psycopg2 |
| Base de datos | PostgreSQL 15 en Amazon RDS (acceso privado) |
| Servidor web | Nginx (reverse proxy + static files) |
| Infraestructura | Terraform + AWS EC2 + VPC + Security Groups |
| CI/CD | GitHub Actions |
| Tests backend | pytest |
| Tests frontend | Vitest + React Testing Library |

### Funcionalidades

- Búsqueda de canciones por nombre, artista o género
- Compra de canciones con validación en frontend y backend
- Gestión de clientes
- Autenticación y roles (admin/usuario)
- Alertas de éxito/error en operaciones

### Arquitectura de Red

```
Internet
  └── EC2 Frontend (IP pública) :80
        ├── Sirve archivos estáticos React desde /var/www/chinook
        └── Nginx proxy /api/* → EC2 Backend (IP privada) :8000
              └── RDS PostgreSQL (solo accesible desde backend SG)
```

### Estructura del Repositorio (Parcial 1)

```
backend/          FastAPI app, rutas, lógica de negocio, tests
frontend/         React app, componentes, tests
infra/
  terraform/      Networking, EC2, Security Groups, RDS
  db/             Scripts de inicialización Chinook PostgreSQL
  scripts/        Bootstrap y deploy scripts
docs/             Guía de deployment completa
.github/workflows/ Pipeline CI/CD
```

### CI/CD Pipeline

Al hacer push a `main`:
1. `backend-test` — instala dependencias y corre pytest
2. `frontend-test-build` — instala, corre vitest y genera build de producción
3. `deploy` — despliega al EC2 frontend y backend vía SSH (ProxyJump)

**Secrets requeridos en GitHub:**
- `SSH_PRIVATE_KEY_B64`
- `SSH_USER`
- `FRONTEND_HOST`
- `BACKEND_PRIVATE_IP`
- `FRONTEND_SERVER_NAME`
- `FRONTEND_BASE_URL`

### Setup Local

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm ci
npm run dev
```

---

## Parcial 2 — Data Warehouse & Analytics sobre AWS

### Objetivo

Diseñar e implementar un sistema de analítica empresarial sobre la base de datos
transaccional Chinook, aplicando los conceptos de Data Warehouse (esquema estrella),
ETL con AWS Glue, almacenamiento analítico con S3 + Athena y visualización con Power BI.

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPA TRANSACCIONAL                          │
│              Amazon RDS PostgreSQL — Base: chinook                  │
│   customer · employee · invoice · invoice_line · track              │
│   album · artist · genre · media_type                               │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  AWS Glue ETL Jobs (JDBC)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE ALMACENAMIENTO                         │
│            s3://chinook-dw-parcial2/   (Parquet + Snappy)           │
│   dim_date/   dim_customer/   dim_track/   fact_sales/year=.../     │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  AWS Athena (Glue Data Catalog)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CAPA ANALÍTICA                                │
│                  Athena DB: chinook_dw                              │
│         4 tablas externas · 4 queries de negocio                    │
└──────────────────────┬──────────────────────────────────────────────┘
                       │  ODBC (Simba Athena Driver)
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                             │
│                  Power BI Desktop                                   │
│    Tracks por día · Artista por mes · Día semana · Mes ventas       │
└─────────────────────────────────────────────────────────────────────┘
```

### Esquema Estrella (Data Warehouse)

```
                    ┌─────────────┐
                    │  dim_date   │
                    │─────────────│
                    │ DateKey (PK)│
                    │ FullDate    │
                    │ Year        │
                    │ Quarter     │
                    │ Month       │
                    │ Day         │
                    │ DayOfWeek   │
                    │ IsHoliday   │
                    └──────┬──────┘
                           │
┌─────────────┐    ┌───────┴──────┐    ┌─────────────┐
│ dim_customer│    │  fact_sales  │    │  dim_track  │
│─────────────│    │──────────────│    │─────────────│
│CustomerKey  ├────│ CustomerKey  │────┤ TrackKey    │
│ FirstName   │    │ TrackKey  (FK│    │ Name        │
│ LastName    │    │InvoiceDateKey│    │ Album       │
│ Company     │    │ EmployeeKey  │    │ Artist      │
│ Country     │    │ Quantity     │    │ Genre       │
│ City        │    │ UnitPrice    │    │ MediaType   │
│ State       │    │ TotalAmount  │    │ Composer    │
│ Email       │    │ year (part.) │    │ Milliseconds│
│ EmployeeKey │    │ month(part.) │    │ UnitPrice   │
│EmployeeName │    │ day  (part.) │    └─────────────┘
│ ReportsTo   │    └──────┬───────┘
└─────────────┘           │
                    ┌──────┴──────┐
                    │  dim_date   │
                    │ (ver arriba)│
                    └─────────────┘
```

### ETL Jobs (AWS Glue)

| Job | Tipo | Tablas origen | Salida S3 |
|-----|------|--------------|-----------|
| `etl-dim-date` | Script Python + holidays | — (generado) | `dim_date/dim_date.parquet` |
| `etl-dim-customer` | Glue ETL (Spark) | customer + employee | `dim_customer/` |
| `etl-dim-track` | Glue ETL (Spark) | track + album + artist + genre + media_type | `dim_track/` |
| `etl-fact-sales` | Glue ETL (Spark) | invoice + invoice_line + customer | `fact_sales/year=.../month=.../day=.../` |

**Decisiones técnicas:**
- `DimDate` usa el paquete `holidays` con feriados de Colombia (2000–2030)
- `FactSales` está particionada por `year/month/day` para eficiencia en Athena
- Todos los jobs usan `G.1X` workers (mínimo costo) con timeout de 20 minutos
- Formato de almacenamiento: **Parquet** con compresión **Snappy**
- Los scripts de Glue usan **Spark JDBC** con credenciales explícitas para compatibilidad con subnets privadas

### Analytics Queries (Athena — chinook_dw)

```sql
-- 1. Tracks vendidos por día
SELECT dd.FullDate, SUM(fs.Quantity) AS tracks_sold
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.FullDate ORDER BY dd.FullDate;

-- 2. Artista más vendido por mes
SELECT dd.Year, dd.Month, dt.Artist, SUM(fs.Quantity) AS total_vendido
FROM fact_sales fs
JOIN dim_date dd  ON fs.InvoiceDateKey = dd.DateKey
JOIN dim_track dt ON fs.TrackKey = dt.TrackKey
GROUP BY dd.Year, dd.Month, dt.Artist
ORDER BY dd.Year, dd.Month, total_vendido DESC;

-- 3. Día de la semana que más se compra
SELECT dd.DayOfWeek,
       CASE dd.DayOfWeek WHEN 0 THEN 'Lunes' WHEN 1 THEN 'Martes'
         WHEN 2 THEN 'Miércoles' WHEN 3 THEN 'Jueves' WHEN 4 THEN 'Viernes'
         WHEN 5 THEN 'Sábado' ELSE 'Domingo' END AS NombreDia,
       SUM(fs.Quantity) AS total_compras
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.DayOfWeek ORDER BY total_compras DESC;

-- 4. Mes con mayor número de ventas
SELECT dd.Month, SUM(fs.TotalAmount) AS total_ventas
FROM fact_sales fs JOIN dim_date dd ON fs.InvoiceDateKey = dd.DateKey
GROUP BY dd.Month ORDER BY total_ventas DESC;
```

### Infraestructura AWS (Parcial 2)

| Recurso | Identificador |
|---------|--------------|
| S3 DW | `s3://chinook-dw-parcial2/` |
| S3 Athena results | `s3://chinook-athena-results/results/` |
| Glue Connection | `chinook-rds-connection` (JDBC PostgreSQL) |
| Glue Database | `chinook_dw` |
| VPC Endpoint S3 | `vpce-0b552a40d7803f3c1` (Gateway) |
| Region | `us-east-1` |
| IAM Role | `LabRole` (Vocareum) |

### Setup del Data Warehouse

**Prerrequisitos:**
- Credenciales AWS configuradas (`aws configure`)
- Python 3.11+ con boto3 instalado
- RDS del Parcial 1 activo

```bash
cd parcial2
pip install -r requirements.txt

# Ejecutar en orden:
python fase1_setup_s3.py       # Crear buckets S3
python fase2_glue_setup.py     # Glue Connection + IAM + Secrets Manager
python fase3_etl_dim_date.py   # ETL DimDate (feriados Colombia)
python fase4y5_final.py        # ETL DimCustomer + DimTrack + FactSales
python fase6_athena.py         # Tablas externas + queries analíticas
```

### Power BI

Conexión vía ODBC (Simba Amazon Athena ODBC Driver 64-bit):

| Campo | Valor |
|-------|-------|
| Region | `us-east-1` |
| S3 Output | `s3://chinook-athena-results/results/` |
| Auth Type | IAM Credentials |
| Schema | `chinook_dw` |

**Reportes implementados:**
1. Tracks vendidos por día — Line chart
2. Artista más vendido por mes — Clustered bar chart
3. Día de la semana con más compras — Bar chart
4. Mes con mayor volumen de ventas — Bar chart

---

## Pruebas Unitarias

### Parcial 1

```bash
# Backend
cd backend && pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend && npm test
```

### Parcial 2 (ETL)

```bash
pytest tests/test_etl.py -v
```

Los tests del ETL validan:
- Formato y rango de `DateKey` (YYYYMMDD)
- Derivación correcta de `Quarter` y `DayOfWeek`
- Integridad de columnas en cada dimensión y la tabla de hechos
- Cálculo de `TotalAmount = Quantity × UnitPrice`
- Consistencia entre `InvoiceDateKey` y columnas de partición `year/month/day`
- Convención de rutas S3 del Data Warehouse

---

## CI/CD

### Parcial 1 — Deploy Pipeline

```
push to main
  ├── backend-test    pytest en ubuntu-latest
  ├── frontend-test   vitest + build en ubuntu-latest
  └── deploy          SSH deploy a EC2 (frontend como bastion para backend)
```

### Parcial 2 — ETL Tests Pipeline

```
push to main
  └── etl-tests       pytest tests/test_etl.py en ubuntu-latest
```

---

## Despliegue Completo — Zero to Working

### Parcial 1

1. Provisionar infraestructura con Terraform (`infra/terraform/`)
2. Bootstrap de servidores EC2 con scripts existentes
3. Inicializar base de datos Chinook en RDS (`infra/db/`)
4. Configurar secrets en GitHub y hacer push para activar CI/CD

### Parcial 2

1. Asegurarse de que el RDS del Parcial 1 esté activo
2. Ejecutar los scripts en `parcial2/` en orden (ver sección Setup)
3. Conectar Power BI con el driver ODBC de Athena

---

## Consideraciones de Arquitectura

### ¿Por qué RDS privado?
El RDS no tiene IP pública. Solo el EC2 backend puede acceder a él vía Security Group.
Esto sigue el modelo de seguridad por capas estándar en producción.

### ¿Por qué Nginx como reverse proxy?
El frontend usa rutas relativas `/api/*`. Nginx en el EC2 frontend reenvía ese tráfico
al EC2 backend por IP privada, evitando exponer el backend directamente a internet.

### ¿Por qué Parquet + Snappy en S3?
Parquet es columnar y Athena cobra por datos escaneados. Parquet reduce
significativamente el volumen leído en queries analíticas. Snappy ofrece buena
compresión con decompresión rápida, equilibrio ideal para analytics.

### ¿Por qué particionar FactSales por year/month/day?
Las queries del parcial filtran por fecha. El particionamiento permite a Athena
hacer partition pruning y escanear solo los archivos relevantes, reduciendo
costo y tiempo de respuesta.

### ¿Por qué DimDate generada y no extraída del RDS?
La dimensión de tiempo debe cubrir un rango completo (2000–2030) independiente
de los datos transaccionales, e incluir atributos como `IsHoliday` que no existen
en la fuente. Por eso se genera programáticamente con el paquete `holidays`.

---

## Autor

**Julian Esteban Rincón Rodríguez**
Estudiante de Ingeniería de Sistemas e Inteligencia Artificial
Universidad Sergio Arboleda — Bogotá, Colombia
GitHub: [@Julian-Rincon](https://github.com/Julian-Rincon)
