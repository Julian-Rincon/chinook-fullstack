# Resumen Parcial 2

Este módulo agrega el pipeline analítico del Parcial 2 al proyecto Chinook
Fullstack. La integración implementa un Data Warehouse en S3 con esquema
estrella, jobs ETL de AWS Glue y consultas analíticas en Athena.

## Componentes

- `fase1_setup_s3.py`: crea los buckets y prefijos base del DW.
- `fase2_glue_setup.py`: crea la base de datos de Glue, el secreto y la conexión JDBC a RDS.
- `fase3_etl_dim_date.py`: genera `DimDate` para el rango 2000-2030.
- `fase4y5_final.py`: registra los jobs Glue para `DimCustomer`, `DimTrack` y `FactSales`.
- `fase6_athena.py`: crea tablas externas en Athena y ejecuta las queries de negocio.
- `inspector.py`: revisa rápidamente datasets en S3 y tablas del Glue Data Catalog.

## Salidas

- `s3://chinook-dw-parcial2/dim_date/`
- `s3://chinook-dw-parcial2/dim_customer/`
- `s3://chinook-dw-parcial2/dim_track/`
- `s3://chinook-dw-parcial2/fact_sales/year=.../month=.../day=.../`

## Validación

Las pruebas unitarias del parcial están en `tests/test_etl.py` y se ejecutan con:

```bash
pytest tests/test_etl.py -v
```
