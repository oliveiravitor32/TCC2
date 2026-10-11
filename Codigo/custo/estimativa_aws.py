"""Apendice D (Quadro 21): custo mensal da arquitetura de referencia (3.12.6.4) na AWS, regiao sa-east-1.

Precos sob demanda em US$ tirados da AWS Price List (consulta em 10/10/2026):
https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<Servico>/current/sa-east-1/index.json
(publicationDate: EC2 09/10/2026, RDS 06/10/2026, EKS 28/09/2026, ElastiCache 14/09/2026,
MSK 11/09/2026, ELB 11/09/2026). Dimensionamento dos autores, sem teste de carga.

    python Codigo/custo/estimativa_aws.py
"""
H = 730  # horas por mes

ITENS = [  # (componente, quantidade, preco unitario, unidade)
    ("EKS plano de controle", 1 * H, 0.10, "h"),
    ("EC2 m7g.xlarge (nos do cluster)", 3 * H, 0.2601, "h"),
    ("EBS gp3 dos nos (3 x 50 GB)", 150, 0.152, "GB-mes"),
    ("MSK kafka.m7g.large", 3 * H, 0.3253, "h"),
    ("MSK armazenamento (3 x 200 GB)", 600, 0.19, "GB-mes"),
    ("ElastiCache cache.m7g.large (Redis)", 2 * H, 0.225, "h"),
    ("RDS PostgreSQL db.m7g.large Multi-AZ", 1 * H, 0.442, "h"),
    ("RDS gp3 Multi-AZ (100 GB)", 100, 0.438, "GB-mes"),
    ("EC2 r7g.large (TimescaleDB)", 2 * H, 0.1704, "h"),
    ("EBS gp3 TimescaleDB (2 x 1000 GB)", 2000, 0.152, "GB-mes"),
    ("Network Load Balancer", 1 * H, 0.034, "h"),
    ("NAT Gateway", 3 * H, 0.093, "h"),
    ("Secrets Manager (20 segredos)", 20, 0.40, "segredo-mes"),
]

total = 0.0
for nome, qtd, preco, un in ITENS:
    custo = qtd * preco
    total += custo
    print(f"{nome:42s} {qtd:8.0f} {un:12s} x {preco:<7} = {custo:9.2f}")
print(f"{'TOTAL (US$/mes)':42s} {total:42.2f}")
