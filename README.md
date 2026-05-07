ReadinessIQ
A full-stack logistics readiness platform that ingests shipment, inventory, maintenance, and supplier data to identify readiness risk, supply constraints, backlog growth, and emerging operational issues.

readiness-iq/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── analytics/
│   │   │   └── kpis.py
│   │   ├── routers/
│   │   │   └── health.py
│   │   └── schemas/
│   ├── scripts/
│   │   └── generate_synthetic_data.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
├── data/
│   ├── raw/
│   └── processed/
├── docker-compose.yml
├── README.md
└── .gitignore

MVP rule

For the first version
Which sites are highest risk?
Which parts are below reorder point?
Which shipments are delayed?
Which suppliers are causing the most delays?
Which sites have growing maintenance backlog?
